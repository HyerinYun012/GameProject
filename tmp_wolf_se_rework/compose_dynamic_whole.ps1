$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing

$scale=4
$work=1024

function New-Transparent([int]$W,[int]$H){$b=[System.Drawing.Bitmap]::new($W,$H,[System.Drawing.Imaging.PixelFormat]::Format32bppArgb);$g=[System.Drawing.Graphics]::FromImage($b);try{$g.CompositingMode=[System.Drawing.Drawing2D.CompositingMode]::SourceCopy;$g.Clear([System.Drawing.Color]::Transparent)}finally{$g.Dispose()};return $b}
function Upscale([System.Drawing.Bitmap]$Small){$b=New-Transparent $work $work;$g=[System.Drawing.Graphics]::FromImage($b);try{$g.CompositingMode=[System.Drawing.Drawing2D.CompositingMode]::SourceCopy;$g.CompositingQuality=[System.Drawing.Drawing2D.CompositingQuality]::HighQuality;$g.InterpolationMode=[System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic;$g.PixelOffsetMode=[System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality;$g.DrawImage($Small,[System.Drawing.Rectangle]::new(0,0,$work,$work),[System.Drawing.Rectangle]::new(0,0,256,256),[System.Drawing.GraphicsUnit]::Pixel)}finally{$g.Dispose()};return $b}
function MapX([double]$X){return 64.0+($X-220.0)*128.0/740.0}
function MapY([double]$Y){return 88.0+($Y-430.0)*160.0/700.0}
function Lerp([double]$A,[double]$B,[double]$T){return $A+($B-$A)*$T}

function New-LimbPath([double]$Ax,[double]$Ay,[double]$Px,[double]$Py,[double]$Width){
  $p=[System.Drawing.Drawing2D.GraphicsPath]::new();$p.AddLine([single]($Ax*$scale),[single]($Ay*$scale),[single]($Px*$scale),[single]($Py*$scale))
  $pen=[System.Drawing.Pen]::new([System.Drawing.Color]::White,[single]($Width*$scale));try{$pen.StartCap=[System.Drawing.Drawing2D.LineCap]::Round;$pen.EndCap=[System.Drawing.Drawing2D.LineCap]::Round;$pen.LineJoin=[System.Drawing.Drawing2D.LineJoin]::Round;$p.Widen($pen)}finally{$pen.Dispose()}
  $p.AddEllipse([single](($Px-$Width*.62)*$scale),[single](($Py-$Width*.48)*$scale),[single]($Width*1.24*$scale),[single]($Width*.96*$scale));return $p
}

function New-BodyPath {
  $coords=@(@(61,112),@(66,99),@(78,91),@(96,85),@(120,85),@(142,96),@(157,108),@(174,111),@(187,122),@(194,141),@(195,163),@(190,179),@(178,192),@(161,193),@(148,180),@(137,172),@(121,167),@(103,165),@(86,166),@(70,161),@(61,148))
  $pts=[System.Drawing.PointF[]]::new($coords.Count);for($i=0;$i -lt $coords.Count;$i++){$pts[$i]=[System.Drawing.PointF]::new([single]($coords[$i][0]*$scale),[single]($coords[$i][1]*$scale))}
  $p=[System.Drawing.Drawing2D.GraphicsPath]::new();$p.AddPolygon($pts);return $p
}

function Extract([System.Drawing.Bitmap]$Source,[System.Drawing.Drawing2D.GraphicsPath]$Mask){$b=New-Transparent $work $work;$g=[System.Drawing.Graphics]::FromImage($b);try{$g.CompositingMode=[System.Drawing.Drawing2D.CompositingMode]::SourceCopy;$g.SetClip($Mask);$g.DrawImageUnscaled($Source,0,0)}finally{$g.Dispose()};return $b}

$phase=@(0.0,.34,.68,1.0,.68,.34)
$nearLift=@(4,32,38,0,-18,-28)
$farLift=@(0,-12,-22,34,47,58)
$nearSide=@(0,-20,-45,0,-45,-45)
$farSide=@(0,20,45,0,45,45)
$nearForeExtra=@(0,0,-25,0,-25,-100)
$farForeExtra=@(0,0,25,0,25,100)

$nh=@{px=360;py=690;sx=285;sy=870;fx=430;fy=930}
$fh=@{px=475;py=720;sx=475;sy=945;bx=350;by=885}
$ff=@{px=610;py=770;sx=650;sy=1010;fx=780;fy=1045}
$nf=@{px=735;py=805;sx=890;sy=1090;bx=630;by=1030}

$preview=New-Transparent 1536 256
try{$pg=[System.Drawing.Graphics]::FromImage($preview);try{$pg.CompositingMode=[System.Drawing.Drawing2D.CompositingMode]::SourceCopy;$pg.Clear([System.Drawing.Color]::Transparent)
  for($f=0;$f -lt 6;$f++){
    $poseSmall=[System.Drawing.Bitmap]::new((Join-Path $PSScriptRoot ('coherent_SE_{0}.png' -f $f)))
    $bodySmall=[System.Drawing.Bitmap]::new((Join-Path $PSScriptRoot ('sequence_SE_{0}.png' -f $f)))
    try{$pose=Upscale $poseSmall;$body=Upscale $bodySmall
      try{$t=$phase[$f]
        $nhx=(Lerp $nh.fx $nh.sx $t)+$nearSide[$f];$nhy=(Lerp $nh.fy $nh.sy $t)+$nearLift[$f]
        $fhx=(Lerp $fh.bx $fh.sx $t)+$farSide[$f];$fhy=(Lerp $fh.by $fh.sy $t)+$farLift[$f]
        $ffx=(Lerp $ff.sx $ff.fx $t)+$farSide[$f]+$farForeExtra[$f];$ffy=(Lerp $ff.sy $ff.fy $t)+$farLift[$f]
        $nfx=(Lerp $nf.sx $nf.bx $t)+$nearSide[$f]+$nearForeExtra[$f];$nfy=(Lerp $nf.sy $nf.by $t)+$nearLift[$f]

        $nhPath=New-LimbPath (MapX $nh.px) (MapY $nh.py) (MapX $nhx) (MapY $nhy) 22
        $fhPath=New-LimbPath (MapX $fh.px) (MapY $fh.py) (MapX $fhx) (MapY $fhy) 19
        $ffPath=New-LimbPath (MapX $ff.px) (MapY $ff.py) (MapX $ffx) (MapY $ffy) 19
        $nfPath=New-LimbPath (MapX $nf.px) (MapY $nf.py) (MapX $nfx) (MapY $nfy) 23
        $bodyPath=New-BodyPath
        try{$nhLayer=Extract $pose $nhPath;$fhLayer=Extract $pose $fhPath;$ffLayer=Extract $pose $ffPath;$nfLayer=Extract $pose $nfPath;$bodyLayer=Extract $body $bodyPath
          try{$hi=New-Transparent $work $work;try{$g=[System.Drawing.Graphics]::FromImage($hi);try{$g.CompositingMode=[System.Drawing.Drawing2D.CompositingMode]::SourceOver;$g.CompositingQuality=[System.Drawing.Drawing2D.CompositingQuality]::HighQuality;$g.InterpolationMode=[System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic;$g.PixelOffsetMode=[System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
            $g.DrawImageUnscaled($fhLayer,0,0);$g.DrawImageUnscaled($ffLayer,0,0);$g.DrawImageUnscaled($nhLayer,0,0);$g.DrawImageUnscaled($nfLayer,0,0);$g.DrawImageUnscaled($bodyLayer,0,0)
          }finally{$g.Dispose()}
            $out=New-Transparent 256 256;try{$down=[System.Drawing.Graphics]::FromImage($out);try{$down.CompositingMode=[System.Drawing.Drawing2D.CompositingMode]::SourceCopy;$down.CompositingQuality=[System.Drawing.Drawing2D.CompositingQuality]::HighQuality;$down.InterpolationMode=[System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic;$down.PixelOffsetMode=[System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality;$down.DrawImage($hi,[System.Drawing.Rectangle]::new(0,0,256,256),[System.Drawing.Rectangle]::new(0,0,$work,$work),[System.Drawing.GraphicsUnit]::Pixel)}finally{$down.Dispose()}
              for($y=0;$y -lt 256;$y++){for($x=0;$x -lt 256;$x++){$c=$out.GetPixel($x,$y);if($c.A -lt 16){$out.SetPixel($x,$y,[System.Drawing.Color]::Transparent)}}}
              $path=Join-Path $PSScriptRoot ('sequence_pace_SE_{0}.png' -f $f);$out.Save($path,[System.Drawing.Imaging.ImageFormat]::Png);$pg.DrawImageUnscaled($out,$f*256,0)
            }finally{$out.Dispose()}
          }finally{$hi.Dispose()}
        }finally{$nhLayer.Dispose();$fhLayer.Dispose();$ffLayer.Dispose();$nfLayer.Dispose();$bodyLayer.Dispose()}
        }finally{$nhPath.Dispose();$fhPath.Dispose();$ffPath.Dispose();$nfPath.Dispose();$bodyPath.Dispose()}
      }finally{$pose.Dispose();$body.Dispose()}
    }finally{$poseSmall.Dispose();$bodySmall.Dispose()}
  }
}finally{$pg.Dispose()};$preview.Save((Join-Path $PSScriptRoot 'preview_sequence_pace_SE.png'),[System.Drawing.Imaging.ImageFormat]::Png)}finally{$preview.Dispose()}
