$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing

$sourcePath=(Resolve-Path (Join-Path $PSScriptRoot 'raw_camel_f0.png')).Path
$targetColor=[System.Drawing.Color]::FromArgb(97,88,82)

function New-Transparent([int]$W,[int]$H){$b=[System.Drawing.Bitmap]::new($W,$H,[System.Drawing.Imaging.PixelFormat]::Format32bppArgb);$g=[System.Drawing.Graphics]::FromImage($b);try{$g.CompositingMode=[System.Drawing.Drawing2D.CompositingMode]::SourceCopy;$g.Clear([System.Drawing.Color]::Transparent)}finally{$g.Dispose()};return $b}

function New-LimbMask([double]$Ax,[double]$Ay,[double]$Px,[double]$Py,[double]$Width){
    $p=[System.Drawing.Drawing2D.GraphicsPath]::new();$p.AddLine([single]$Ax,[single]$Ay,[single]$Px,[single]$Py)
    $pen=[System.Drawing.Pen]::new([System.Drawing.Color]::White,[single]$Width);try{$pen.StartCap=[System.Drawing.Drawing2D.LineCap]::Round;$pen.EndCap=[System.Drawing.Drawing2D.LineCap]::Round;$pen.LineJoin=[System.Drawing.Drawing2D.LineJoin]::Round;$p.Widen($pen)}finally{$pen.Dispose()}
    $p.AddEllipse([single]($Px-$Width*0.62),[single]($Py-$Width*0.48),[single]($Width*1.24),[single]($Width*0.96));return $p
}

function New-BodyMask {
    $coords=@(@(220,620),@(245,555),@(315,500),@(405,455),@(510,430),@(600,448),@(690,500),@(755,560),@(830,605),@(900,650),@(950,735),@(965,825),@(945,900),@(890,950),@(815,965),@(755,925),@(710,860),@(655,810),@(585,795),@(510,785),@(430,775),@(355,760),@(285,735),@(230,700))
    $pts=[System.Drawing.PointF[]]::new($coords.Count);for($i=0;$i -lt $coords.Count;$i++){$pts[$i]=[System.Drawing.PointF]::new([single]$coords[$i][0],[single]$coords[$i][1])}
    $p=[System.Drawing.Drawing2D.GraphicsPath]::new();$p.AddPolygon($pts);return $p
}

function Extract([System.Drawing.Bitmap]$Source,[System.Drawing.Drawing2D.GraphicsPath]$Mask){$b=New-Transparent $Source.Width $Source.Height;$g=[System.Drawing.Graphics]::FromImage($b);try{$g.CompositingMode=[System.Drawing.Drawing2D.CompositingMode]::SourceCopy;$g.SetClip($Mask);$g.DrawImageUnscaled($Source,0,0)}finally{$g.Dispose()};return $b}

function Draw-Limb {
    param([System.Drawing.Graphics]$Graphics,[System.Drawing.Bitmap]$Layer,[double]$PivotX,[double]$PivotY,[double]$SourcePawX,[double]$SourcePawY,[double]$TargetPawX,[double]$TargetPawY)
    $sx=$SourcePawX-$PivotX;$sy=$SourcePawY-$PivotY;$tx=$TargetPawX-$PivotX;$ty=$TargetPawY-$PivotY
    $sourceLength=[Math]::Sqrt($sx*$sx+$sy*$sy);$targetLength=[Math]::Sqrt($tx*$tx+$ty*$ty)
    $lengthScale=$targetLength/$sourceLength

    # Map the source limb axis onto the target limb axis while preserving the
    # perpendicular width.  Uniform scaling made shortened limbs unnaturally
    # thin and extended limbs club-shaped; this affine basis transform changes
    # length only, so every frame keeps the original painted leg thickness.
    $sux=$sx/$sourceLength;$suy=$sy/$sourceLength;$svx=-$suy;$svy=$sux
    $tux=$tx/$targetLength;$tuy=$ty/$targetLength;$tvx=-$tuy;$tvy=$tux
    $widthScale=1.12
    $a11=$lengthScale*$tux*$sux+$widthScale*$tvx*$svx
    $a12=$lengthScale*$tux*$suy+$widthScale*$tvx*$svy
    $a21=$lengthScale*$tuy*$sux+$widthScale*$tvy*$svx
    $a22=$lengthScale*$tuy*$suy+$widthScale*$tvy*$svy
    $dx=$PivotX-($a11*$PivotX+$a12*$PivotY)
    $dy=$PivotY-($a21*$PivotX+$a22*$PivotY)

    $matrix=[System.Drawing.Drawing2D.Matrix]::new([single]$a11,[single]$a21,[single]$a12,[single]$a22,[single]$dx,[single]$dy)
    $state=$Graphics.Save()
    try{$Graphics.Transform=$matrix;$Graphics.DrawImageUnscaled($Layer,0,0)}
    finally{$Graphics.Restore($state);$matrix.Dispose()}
}

function Draw-BodyDynamic {
    param(
        [System.Drawing.Graphics]$Graphics,
        [System.Drawing.Bitmap]$Layer,
        [double]$PivotX,
        [double]$PivotY,
        [double]$TranslateX,
        [double]$TranslateY,
        [double]$Angle,
        [double]$ScaleX,
        [double]$ScaleY
    )
    $state=$Graphics.Save()
    try{
        $Graphics.TranslateTransform([single]($PivotX+$TranslateX),[single]($PivotY+$TranslateY))
        $Graphics.RotateTransform([single]$Angle)
        $Graphics.ScaleTransform([single]$ScaleX,[single]$ScaleY)
        $Graphics.TranslateTransform(-[single]$PivotX,-[single]$PivotY)
        $Graphics.DrawImageUnscaled($Layer,0,0)
    }
    finally{$Graphics.Restore($state)}
}

function Lerp([double]$A,[double]$B,[double]$T){return $A+($B-$A)*$T}

function Normalize-Color([System.Drawing.Bitmap]$Bitmap){
    [long]$sr=0;[long]$sg=0;[long]$sb=0;[long]$n=0;for($y=0;$y -lt 256;$y++){for($x=0;$x -lt 256;$x++){$c=$Bitmap.GetPixel($x,$y);if($c.A -ge 64){$sr+=$c.R;$sg+=$c.G;$sb+=$c.B;$n++}}};if($n -eq 0){return}
    $dr=$targetColor.R-[int]($sr/$n);$dg=$targetColor.G-[int]($sg/$n);$db=$targetColor.B-[int]($sb/$n)
    for($y=0;$y -lt 256;$y++){for($x=0;$x -lt 256;$x++){$c=$Bitmap.GetPixel($x,$y);if($c.A -lt 16){$Bitmap.SetPixel($x,$y,[System.Drawing.Color]::Transparent);continue};$r=[Math]::Max(0,[Math]::Min(255,$c.R+$dr));$g=[Math]::Max(0,[Math]::Min(255,$c.G+$dg));$b=[Math]::Max(0,[Math]::Min(255,$c.B+$db));$Bitmap.SetPixel($x,$y,[System.Drawing.Color]::FromArgb($c.A,$r,$g,$b))}}
}

function Get-ColorOffset([System.Drawing.Bitmap]$Bitmap){
    [long]$sr=0;[long]$sg=0;[long]$sb=0;[long]$n=0
    for($y=0;$y -lt 256;$y++){for($x=0;$x -lt 256;$x++){$c=$Bitmap.GetPixel($x,$y);if($c.A -ge 64){$sr+=$c.R;$sg+=$c.G;$sb+=$c.B;$n++}}}
    if($n -eq 0){throw 'Cannot calculate color offset for an empty frame.'}
    return [pscustomobject]@{R=$targetColor.R-[int]($sr/$n);G=$targetColor.G-[int]($sg/$n);B=$targetColor.B-[int]($sb/$n)}
}

function Apply-ColorOffset([System.Drawing.Bitmap]$Bitmap,[pscustomobject]$Offset){
    for($y=0;$y -lt 256;$y++){for($x=0;$x -lt 256;$x++){$c=$Bitmap.GetPixel($x,$y);if($c.A -lt 16){$Bitmap.SetPixel($x,$y,[System.Drawing.Color]::Transparent);continue};$r=[Math]::Max(0,[Math]::Min(255,$c.R+$Offset.R));$g=[Math]::Max(0,[Math]::Min(255,$c.G+$Offset.G));$b=[Math]::Max(0,[Math]::Min(255,$c.B+$Offset.B));$Bitmap.SetPixel($x,$y,[System.Drawing.Color]::FromArgb($c.A,$r,$g,$b))}}
}

function Get-Bounds([System.Drawing.Bitmap]$Bitmap){$minX=256;$minY=256;$maxX=-1;$maxY=-1;for($y=0;$y -lt 256;$y++){for($x=0;$x -lt 256;$x++){if($Bitmap.GetPixel($x,$y).A -ge 16){if($x -lt $minX){$minX=$x};if($x -gt $maxX){$maxX=$x};if($y -lt $minY){$minY=$y};if($y -gt $maxY){$maxY=$y}}}};return [System.Drawing.Rectangle]::new($minX,$minY,$maxX-$minX+1,$maxY-$minY+1)}

$source=[System.Drawing.Bitmap]::new($sourcePath);try{
    # Fixed physical identity for all six frames.
    $nearHind=[pscustomobject]@{PivotX=360;PivotY=690;PawX=285;PawY=870;ForwardX=430;ForwardY=930;Width=85}
    $farHind =[pscustomobject]@{PivotX=475;PivotY=720;PawX=475;PawY=945;BackX=350;BackY=885;Width=105}
    $farFore =[pscustomobject]@{PivotX=610;PivotY=770;PawX=650;PawY=1010;ForwardX=780;ForwardY=1045;Width=90}
    $nearFore=[pscustomobject]@{PivotX=735;PivotY=805;PawX=890;PawY=1090;BackX=630;BackY=1030;Width=120}

    $nhMask=New-LimbMask $nearHind.PivotX $nearHind.PivotY $nearHind.PawX $nearHind.PawY $nearHind.Width
    $fhMask=New-LimbMask $farHind.PivotX $farHind.PivotY $farHind.PawX $farHind.PawY $farHind.Width
    $ffMask=New-LimbMask $farFore.PivotX $farFore.PivotY $farFore.PawX $farFore.PawY $farFore.Width
    $nfMask=New-LimbMask $nearFore.PivotX $nearFore.PivotY $nearFore.PawX $nearFore.PawY $nearFore.Width
    $bodyMask=New-BodyMask
    try{
        $nhLayer=Extract $source $nhMask;$fhLayer=Extract $source $fhMask;$ffLayer=Extract $source $ffMask;$nfLayer=Extract $source $nfMask;$bodyLayer=Extract $source $bodyMask
        try{
            $phase=@(0.0,0.34,0.68,1.0,0.68,0.34)
            $nearLift=@(4,32,38,0,-18,-28)
            $farLift=@(0,-12,-22,34,47,58)
            $nearSide=@(0,-45,-45,0,-45,-45)
            $farSide=@(0,45,45,0,45,45)
            $nearForeExtra=@(0,-100,-50,0,-50,-100)
            $farForeExtra=@(0,100,50,0,50,100)
            # Coherent upper-body cycle. Contact frames compress and settle;
            # mid-stride frames lengthen and rise. The same painted identity is
            # retained while shoulders, hips, spine, head, and tail all move.
            $bodyX=@(-12,0,12,12,0,-12)
            $bodyY=@(14,0,-14,14,0,-14)
            $bodyAngle=@(-1.00,0.0,1.00,1.00,0.0,-1.00)
            $bodyScaleX=@(0.980,1.000,1.020,0.980,1.000,1.020)
            $bodyScaleY=@(1.015,1.000,0.985,1.015,1.000,0.985)
            $commonColorOffset=$null
            $preview=New-Transparent 1536 256;try{$pg=[System.Drawing.Graphics]::FromImage($preview);try{$pg.CompositingMode=[System.Drawing.Drawing2D.CompositingMode]::SourceOver
                for($f=0;$f -lt 6;$f++){
                    $t=$phase[$f]
                    # t=0: right/near pair forward, left/far pair back.
                    # t=1: exact opposite contact pair.
                    $nhX=(Lerp $nearHind.ForwardX $nearHind.PawX $t)+$nearSide[$f];$nhY=(Lerp $nearHind.ForwardY $nearHind.PawY $t)+$nearLift[$f]
                    $nfX=(Lerp $nearFore.PawX $nearFore.BackX $t)+$nearSide[$f]+$nearForeExtra[$f];$nfY=(Lerp $nearFore.PawY $nearFore.BackY $t)+$nearLift[$f]
                    $fhX=(Lerp $farHind.BackX $farHind.PawX $t)+$farSide[$f];$fhY=(Lerp $farHind.BackY $farHind.PawY $t)+$farLift[$f]
                    $ffX=(Lerp $farFore.PawX $farFore.ForwardX $t)+$farSide[$f]+$farForeExtra[$f];$ffY=(Lerp $farFore.PawY $farFore.ForwardY $t)+$farLift[$f]

                    $hi=New-Transparent $source.Width $source.Height;try{$g=[System.Drawing.Graphics]::FromImage($hi);try{
                        $g.CompositingMode=[System.Drawing.Drawing2D.CompositingMode]::SourceOver;$g.CompositingQuality=[System.Drawing.Drawing2D.CompositingQuality]::HighQuality;$g.InterpolationMode=[System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic;$g.PixelOffsetMode=[System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality;$g.SmoothingMode=[System.Drawing.Drawing2D.SmoothingMode]::HighQuality
                        # Draw fixed far/near identities first, then cover their roots
                        # with the unchanged body so all four attach cleanly.
                        Draw-Limb $g $fhLayer $farHind.PivotX $farHind.PivotY $farHind.PawX $farHind.PawY $fhX $fhY
                        Draw-Limb $g $ffLayer $farFore.PivotX $farFore.PivotY $farFore.PawX $farFore.PawY $ffX $ffY
                        Draw-Limb $g $nhLayer $nearHind.PivotX $nearHind.PivotY $nearHind.PawX $nearHind.PawY $nhX $nhY
                        Draw-Limb $g $nfLayer $nearFore.PivotX $nearFore.PivotY $nearFore.PawX $nearFore.PawY $nfX $nfY
                        Draw-BodyDynamic $g $bodyLayer 600 720 $bodyX[$f] $bodyY[$f] $bodyAngle[$f] $bodyScaleX[$f] $bodyScaleY[$f]

                        # Restore only the lower front-leg segments over the
                        # chest overlap so the far paw never reads as floating.
                        # The upper joints remain hidden under the body fur.
                        $lowerState=$g.Save()
                        try{
                            $g.SetClip([System.Drawing.Rectangle]::new(0,800,$source.Width,$source.Height-800))
                            Draw-Limb $g $ffLayer $farFore.PivotX $farFore.PivotY $farFore.PawX $farFore.PawY $ffX $ffY
                            Draw-Limb $g $nfLayer $nearFore.PivotX $nearFore.PivotY $nearFore.PawX $nearFore.PawY $nfX $nfY
                        }
                        finally{$g.Restore($lowerState)}
                    }finally{$g.Dispose()}
                        $small=New-Transparent 256 256;try{$down=[System.Drawing.Graphics]::FromImage($small);try{
                            $down.CompositingMode=[System.Drawing.Drawing2D.CompositingMode]::SourceCopy;$down.CompositingQuality=[System.Drawing.Drawing2D.CompositingQuality]::HighQuality;$down.InterpolationMode=[System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic;$down.PixelOffsetMode=[System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
                            $down.DrawImage($hi,[System.Drawing.Rectangle]::new(64,88,128,160),[System.Drawing.Rectangle]::new(220,430,740,700),[System.Drawing.GraphicsUnit]::Pixel)
                        }finally{$down.Dispose()}
                            if($null -eq $commonColorOffset){$commonColorOffset=Get-ColorOffset $small}
                            Apply-ColorOffset $small $commonColorOffset
                            $out=Join-Path $PSScriptRoot ('coherent_SE_{0}.png' -f $f);$small.Save($out,[System.Drawing.Imaging.ImageFormat]::Png);$pg.DrawImageUnscaled($small,$f*256,0)
                            $b=Get-Bounds $small;Write-Output ('f{0}: t={1:N2} bbox={2},{3},{4},{5} bottom={6}' -f $f,$t,$b.X,$b.Y,$b.Width,$b.Height,($b.Bottom-1))
                        }finally{$small.Dispose()}
                    }finally{$hi.Dispose()}
                }
            }finally{$pg.Dispose()};$preview.Save((Join-Path $PSScriptRoot 'preview_coherent_SE.png'),[System.Drawing.Imaging.ImageFormat]::Png)}finally{$preview.Dispose()}
        }finally{$nhLayer.Dispose();$fhLayer.Dispose();$ffLayer.Dispose();$nfLayer.Dispose();$bodyLayer.Dispose()}
    }finally{$nhMask.Dispose();$fhMask.Dispose();$ffMask.Dispose();$nfMask.Dispose();$bodyMask.Dispose()}
}finally{$source.Dispose()}
