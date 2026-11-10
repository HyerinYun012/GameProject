$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing

$target=[System.Drawing.Color]::FromArgb(97,88,82)

function Get-AlphaBounds([System.Drawing.Bitmap]$Bitmap,[int]$Threshold=64){
  $minX=$Bitmap.Width;$minY=$Bitmap.Height;$maxX=-1;$maxY=-1
  for($y=0;$y -lt $Bitmap.Height;$y++){for($x=0;$x -lt $Bitmap.Width;$x++){if($Bitmap.GetPixel($x,$y).A -ge $Threshold){if($x -lt $minX){$minX=$x};if($x -gt $maxX){$maxX=$x};if($y -lt $minY){$minY=$y};if($y -gt $maxY){$maxY=$y}}}}
  if($maxX -lt 0){throw 'No opaque pixels.'}
  return [System.Drawing.Rectangle]::new($minX,$minY,$maxX-$minX+1,$maxY-$minY+1)
}

function Normalize-Color([System.Drawing.Bitmap]$Bitmap){
  [long]$sr=0;[long]$sg=0;[long]$sb=0;[long]$n=0
  for($y=0;$y -lt 256;$y++){for($x=0;$x -lt 256;$x++){$c=$Bitmap.GetPixel($x,$y);if($c.A -ge 64){$sr+=$c.R;$sg+=$c.G;$sb+=$c.B;$n++}}}
  $dr=$target.R-[int]($sr/$n);$dg=$target.G-[int]($sg/$n);$db=$target.B-[int]($sb/$n)
  for($y=0;$y -lt 256;$y++){for($x=0;$x -lt 256;$x++){$c=$Bitmap.GetPixel($x,$y);if($c.A -lt 24){$Bitmap.SetPixel($x,$y,[System.Drawing.Color]::Transparent);continue};$r=[Math]::Max(0,[Math]::Min(255,$c.R+$dr));$g=[Math]::Max(0,[Math]::Min(255,$c.G+$dg));$b=[Math]::Max(0,[Math]::Min(255,$c.B+$db));$Bitmap.SetPixel($x,$y,[System.Drawing.Color]::FromArgb($c.A,$r,$g,$b))}}
}

$preview=[System.Drawing.Bitmap]::new(1536,256,[System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
try{$pg=[System.Drawing.Graphics]::FromImage($preview);try{$pg.CompositingMode=[System.Drawing.Drawing2D.CompositingMode]::SourceCopy;$pg.Clear([System.Drawing.Color]::Transparent)
  for($f=0;$f -lt 6;$f++){
    $src=[System.Drawing.Bitmap]::new((Join-Path $PSScriptRoot ('whole_SE_{0}_raw.png' -f $f)))
    try{$bounds=Get-AlphaBounds $src 64
      $out=[System.Drawing.Bitmap]::new(256,256,[System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
      try{$g=[System.Drawing.Graphics]::FromImage($out);try{$g.CompositingMode=[System.Drawing.Drawing2D.CompositingMode]::SourceCopy;$g.CompositingQuality=[System.Drawing.Drawing2D.CompositingQuality]::HighQuality;$g.InterpolationMode=[System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic;$g.PixelOffsetMode=[System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality;$g.Clear([System.Drawing.Color]::Transparent)
        $g.DrawImage($src,[System.Drawing.Rectangle]::new(64,88,128,160),$bounds,[System.Drawing.GraphicsUnit]::Pixel)
      }finally{$g.Dispose()}
        Normalize-Color $out
        $path=Join-Path $PSScriptRoot ('whole_norm_SE_{0}.png' -f $f);$out.Save($path,[System.Drawing.Imaging.ImageFormat]::Png);$pg.DrawImageUnscaled($out,$f*256,0)
        Write-Output ('f{0}: source={1},{2},{3},{4}' -f $f,$bounds.X,$bounds.Y,$bounds.Width,$bounds.Height)
      }finally{$out.Dispose()}
    }finally{$src.Dispose()}
  }
}finally{$pg.Dispose()};$preview.Save((Join-Path $PSScriptRoot 'preview_whole_norm_SE.png'),[System.Drawing.Imaging.ImageFormat]::Png)}finally{$preview.Dispose()}
