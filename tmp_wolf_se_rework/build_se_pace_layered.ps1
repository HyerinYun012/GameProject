$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$scale = 4
$workSize = 1024
$sourcePaths = 0..5 | ForEach-Object { (Resolve-Path (Join-Path $PSScriptRoot ('mirror_SW_to_SE_{0}.png' -f $_))).Path }

$nearHindPaws = @(@(66,200), @(84,209), @(98,212), @(79,197), @(84,210), @(103,215))
$farHindPaws  = @(@(112,185),@(112,196),@(121,211),@(119,211),@(113,209),@(126,213))
$farForePaws  = @(@(128,205),@(151,210),@(165,224),@(145,221),@(181,218),@(183,220))
$nearForePaws = @(@(198,231),@(176,230),@(148,228),@(174,231),@(150,235),@(166,231))

function New-TransparentBitmap([int]$Width,[int]$Height){
    $b=[System.Drawing.Bitmap]::new($Width,$Height,[System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $g=[System.Drawing.Graphics]::FromImage($b); try{$g.CompositingMode=[System.Drawing.Drawing2D.CompositingMode]::SourceCopy;$g.Clear([System.Drawing.Color]::Transparent)}finally{$g.Dispose()}; return $b
}

function New-Upscaled([string]$Path){
    $small=[System.Drawing.Bitmap]::new($Path); try{
        $large=New-TransparentBitmap $workSize $workSize; $g=[System.Drawing.Graphics]::FromImage($large); try{
            $g.CompositingMode=[System.Drawing.Drawing2D.CompositingMode]::SourceCopy
            $g.CompositingQuality=[System.Drawing.Drawing2D.CompositingQuality]::HighQuality
            $g.InterpolationMode=[System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
            $g.PixelOffsetMode=[System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
            $g.DrawImage($small,[System.Drawing.Rectangle]::new(0,0,$workSize,$workSize),[System.Drawing.Rectangle]::new(0,0,256,256),[System.Drawing.GraphicsUnit]::Pixel)
        }finally{$g.Dispose()}; return $large
    }finally{$small.Dispose()}
}

function New-LineMask([double]$Ax,[double]$Ay,[double]$Px,[double]$Py,[double]$Width){
    $p=[System.Drawing.Drawing2D.GraphicsPath]::new()
    $p.AddLine([single]($Ax*$scale),[single]($Ay*$scale),[single]($Px*$scale),[single]($Py*$scale))
    $pen=[System.Drawing.Pen]::new([System.Drawing.Color]::White,[single]($Width*$scale)); try{
        $pen.StartCap=[System.Drawing.Drawing2D.LineCap]::Round;$pen.EndCap=[System.Drawing.Drawing2D.LineCap]::Round;$pen.LineJoin=[System.Drawing.Drawing2D.LineJoin]::Round;$p.Widen($pen)
    }finally{$pen.Dispose()}
    $rx=$Width*0.62*$scale;$ry=$Width*0.48*$scale
    $p.AddEllipse([single]($Px*$scale-$rx),[single]($Py*$scale-$ry),[single](2*$rx),[single](2*$ry))
    return $p
}

function New-BodyMask {
    $coords=@(@(42,110),@(52,84),@(81,62),@(119,60),@(154,67),@(184,79),@(203,95),@(212,121),@(211,150),@(203,171),@(190,186),@(172,191),@(155,183),@(145,170),@(135,159),@(115,156),@(95,155),@(75,158),@(57,164),@(45,151))
    $pts=[System.Drawing.PointF[]]::new($coords.Count);for($i=0;$i -lt $coords.Count;$i++){$pts[$i]=[System.Drawing.PointF]::new([single]($coords[$i][0]*$scale),[single]($coords[$i][1]*$scale))}
    $p=[System.Drawing.Drawing2D.GraphicsPath]::new();$p.AddPolygon($pts);return $p
}

function Extract([System.Drawing.Bitmap]$Source,[System.Drawing.Drawing2D.GraphicsPath]$Mask){
    $layer=New-TransparentBitmap $workSize $workSize;$g=[System.Drawing.Graphics]::FromImage($layer);try{$g.CompositingMode=[System.Drawing.Drawing2D.CompositingMode]::SourceCopy;$g.SetClip($Mask);$g.DrawImageUnscaled($Source,0,0)}finally{$g.Dispose()};return $layer
}

function Normalize-Color([System.Drawing.Bitmap]$Bitmap){
    [long]$sr=0;[long]$sg=0;[long]$sb=0;[long]$n=0
    for($y=0;$y -lt 256;$y++){for($x=0;$x -lt 256;$x++){$c=$Bitmap.GetPixel($x,$y);if($c.A -ge 64){$sr+=$c.R;$sg+=$c.G;$sb+=$c.B;$n++}}}
    if($n -eq 0){return}
    $dr=97-[int]($sr/$n);$dg=88-[int]($sg/$n);$db=82-[int]($sb/$n)
    for($y=0;$y -lt 256;$y++){for($x=0;$x -lt 256;$x++){$c=$Bitmap.GetPixel($x,$y);if($c.A -lt 16){$Bitmap.SetPixel($x,$y,[System.Drawing.Color]::Transparent);continue};$r=[Math]::Max(0,[Math]::Min(255,$c.R+$dr));$g=[Math]::Max(0,[Math]::Min(255,$c.G+$dg));$b=[Math]::Max(0,[Math]::Min(255,$c.B+$db));$Bitmap.SetPixel($x,$y,[System.Drawing.Color]::FromArgb($c.A,$r,$g,$b))}}
}

function Get-Bounds([System.Drawing.Bitmap]$Bitmap){$minX=256;$minY=256;$maxX=-1;$maxY=-1;for($y=0;$y -lt 256;$y++){for($x=0;$x -lt 256;$x++){if($Bitmap.GetPixel($x,$y).A -ge 16){if($x -lt $minX){$minX=$x};if($x -gt $maxX){$maxX=$x};if($y -lt $minY){$minY=$y};if($y -gt $maxY){$maxY=$y}}}};return [System.Drawing.Rectangle]::new($minX,$minY,$maxX-$minX+1,$maxY-$minY+1)}

$sources=@();try{
    foreach($p in $sourcePaths){$sources+=New-Upscaled $p}
    $bodyMask=New-BodyMask
    $bodyLayer=Extract $sources[0] $bodyMask
    try{
        # A phase: near/right pair forward; B phase: near/right pair back.
        # Limb source groups are selected in opposite fore/hind phases to turn
        # the original diagonal trot into the requested ipsilateral pace.
        $specs=@(
            [pscustomobject]@{H=4;F=0;NearLift=0;FarLift=0},
            [pscustomobject]@{H=5;F=1;NearLift=-1;FarLift=-3},
            [pscustomobject]@{H=1;F=2;NearLift=0;FarLift=-5},
            [pscustomobject]@{H=0;F=4;NearLift=0;FarLift=0},
            [pscustomobject]@{H=1;F=2;NearLift=-3;FarLift=0},
            [pscustomobject]@{H=5;F=1;NearLift=-5;FarLift=0}
        )
        $preview=New-TransparentBitmap 1536 256;try{$pg=[System.Drawing.Graphics]::FromImage($preview);try{
            $pg.CompositingMode=[System.Drawing.Drawing2D.CompositingMode]::SourceOver
            for($f=0;$f -lt 6;$f++){
                $h=$specs[$f].H;$fo=$specs[$f].F
                $nhMask=New-LineMask 74 145 $nearHindPaws[$h][0] $nearHindPaws[$h][1] 24
                $fhMask=New-LineMask 106 151 $farHindPaws[$h][0] $farHindPaws[$h][1] 22
                $ffMask=New-LineMask 145 158 $farForePaws[$fo][0] $farForePaws[$fo][1] 22
                $nfMask=New-LineMask 160 159 $nearForePaws[$fo][0] $nearForePaws[$fo][1] 26
                try{
                    $nh=Extract $sources[$h] $nhMask;$fh=Extract $sources[$h] $fhMask;$ff=Extract $sources[$fo] $ffMask;$nf=Extract $sources[$fo] $nfMask
                    try{
                        $hi=New-TransparentBitmap $workSize $workSize;try{$g=[System.Drawing.Graphics]::FromImage($hi);try{
                            $g.CompositingMode=[System.Drawing.Drawing2D.CompositingMode]::SourceOver
                            $g.DrawImageUnscaled($fh,0,[int]($specs[$f].FarLift*$scale));$g.DrawImageUnscaled($ff,0,[int]($specs[$f].FarLift*$scale))
                            $g.DrawImageUnscaled($bodyLayer,0,0)
                            $g.DrawImageUnscaled($nh,0,[int]($specs[$f].NearLift*$scale));$g.DrawImageUnscaled($nf,0,[int]($specs[$f].NearLift*$scale))
                        }finally{$g.Dispose()}
                            $small=New-TransparentBitmap 256 256;try{$down=[System.Drawing.Graphics]::FromImage($small);try{
                                $down.CompositingMode=[System.Drawing.Drawing2D.CompositingMode]::SourceCopy;$down.CompositingQuality=[System.Drawing.Drawing2D.CompositingQuality]::HighQuality;$down.InterpolationMode=[System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic;$down.PixelOffsetMode=[System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
                                # One fixed source rectangle keeps body scale and pivot identical.
                                $down.DrawImage($hi,[System.Drawing.Rectangle]::new(64,88,128,160),[System.Drawing.Rectangle]::new(44*$scale,63*$scale,169*$scale,176*$scale),[System.Drawing.GraphicsUnit]::Pixel)
                            }finally{$down.Dispose()}
                                Normalize-Color $small
                                $out=Join-Path $PSScriptRoot ('pace3_SE_{0}.png' -f $f);$small.Save($out,[System.Drawing.Imaging.ImageFormat]::Png);$pg.DrawImageUnscaled($small,$f*256,0)
                                $b=Get-Bounds $small;Write-Output ('f{0}: H={1} F={2} bbox={3},{4},{5},{6} bottom={7}' -f $f,$h,$fo,$b.X,$b.Y,$b.Width,$b.Height,($b.Bottom-1))
                            }finally{$small.Dispose()}
                        }finally{$hi.Dispose()}
                    }finally{$nh.Dispose();$fh.Dispose();$ff.Dispose();$nf.Dispose()}
                }finally{$nhMask.Dispose();$fhMask.Dispose();$ffMask.Dispose();$nfMask.Dispose()}
            }
        }finally{$pg.Dispose()};$preview.Save((Join-Path $PSScriptRoot 'preview_pace3_SE.png'),[System.Drawing.Imaging.ImageFormat]::Png)}finally{$preview.Dispose()}
    }finally{$bodyLayer.Dispose();$bodyMask.Dispose()}
}finally{foreach($s in $sources){if($null -ne $s){$s.Dispose()}}}
