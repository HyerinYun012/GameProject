$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing

$source=[System.Drawing.Bitmap]::new((Resolve-Path (Join-Path $PSScriptRoot 'whole_sequence_raw.png')).Path)
try{
  if($source.Width -ne 2172 -or $source.Height -ne 724){throw "Unexpected sequence size: $($source.Width)x$($source.Height)"}
  $cellWidth=362
  $frames=@()
  [long]$sumR=0;[long]$sumG=0;[long]$sumB=0;[long]$count=0
  for($f=0;$f -lt 6;$f++){
    $minX=$source.Width;$minY=$source.Height;$maxX=-1;$maxY=-1
    $startX=$f*$cellWidth
    for($y=0;$y -lt $source.Height;$y++){for($x=$startX;$x -lt ($startX+$cellWidth);$x++){if($source.GetPixel($x,$y).A -ge 64){if($x -lt $minX){$minX=$x};if($x -gt $maxX){$maxX=$x};if($y -lt $minY){$minY=$y};if($y -gt $maxY){$maxY=$y}}}}
    if($maxX -lt 0){throw "No opaque pixels in frame $f"}
    $bounds=[System.Drawing.Rectangle]::new($minX,$minY,$maxX-$minX+1,$maxY-$minY+1)
    $out=[System.Drawing.Bitmap]::new(256,256,[System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $g=[System.Drawing.Graphics]::FromImage($out)
    try{$g.CompositingMode=[System.Drawing.Drawing2D.CompositingMode]::SourceCopy;$g.CompositingQuality=[System.Drawing.Drawing2D.CompositingQuality]::HighQuality;$g.InterpolationMode=[System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic;$g.PixelOffsetMode=[System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality;$g.Clear([System.Drawing.Color]::Transparent);$g.DrawImage($source,[System.Drawing.Rectangle]::new(64,88,128,160),$bounds,[System.Drawing.GraphicsUnit]::Pixel)}finally{$g.Dispose()}
    for($y=0;$y -lt 256;$y++){for($x=0;$x -lt 256;$x++){$c=$out.GetPixel($x,$y);if($c.A -ge 64){$sumR+=$c.R;$sumG+=$c.G;$sumB+=$c.B;$count++}}}
    $frames+=$out
    Write-Output ('f{0}: source={1},{2},{3},{4}' -f $f,$bounds.X,$bounds.Y,$bounds.Width,$bounds.Height)
  }

  $preview=[System.Drawing.Bitmap]::new(1536,256,[System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
  try{$pg=[System.Drawing.Graphics]::FromImage($preview);try{$pg.CompositingMode=[System.Drawing.Drawing2D.CompositingMode]::SourceCopy;$pg.Clear([System.Drawing.Color]::Transparent)
    for($f=0;$f -lt 6;$f++){$out=$frames[$f]
      [long]$frameR=0;[long]$frameG=0;[long]$frameB=0;[long]$frameCount=0
      for($y=0;$y -lt 256;$y++){for($x=0;$x -lt 256;$x++){$c=$out.GetPixel($x,$y);if($c.A -ge 64){$frameR+=$c.R;$frameG+=$c.G;$frameB+=$c.B;$frameCount++}}}
      $dr=97-[int]($frameR/$frameCount);$dg=88-[int]($frameG/$frameCount);$db=82-[int]($frameB/$frameCount)
      for($y=0;$y -lt 256;$y++){for($x=0;$x -lt 256;$x++){$c=$out.GetPixel($x,$y);if($c.A -lt 16){$out.SetPixel($x,$y,[System.Drawing.Color]::Transparent);continue};$r=[Math]::Max(0,[Math]::Min(255,$c.R+$dr));$gg=[Math]::Max(0,[Math]::Min(255,$c.G+$dg));$b=[Math]::Max(0,[Math]::Min(255,$c.B+$db));$out.SetPixel($x,$y,[System.Drawing.Color]::FromArgb($c.A,$r,$gg,$b))}}
      $path=Join-Path $PSScriptRoot ('sequence_SE_{0}.png' -f $f);$out.Save($path,[System.Drawing.Imaging.ImageFormat]::Png);$pg.DrawImageUnscaled($out,$f*256,0)
    }
  }finally{$pg.Dispose()};$preview.Save((Join-Path $PSScriptRoot 'preview_sequence_SE.png'),[System.Drawing.Imaging.ImageFormat]::Png)}finally{$preview.Dispose()}
  foreach($frame in $frames){$frame.Dispose()}
}finally{$source.Dispose()}
