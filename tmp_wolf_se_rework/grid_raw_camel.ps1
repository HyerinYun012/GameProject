$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
$src=[System.Drawing.Bitmap]::new((Resolve-Path (Join-Path $PSScriptRoot 'raw_camel_f0.png')).Path)
try{
  $out=[System.Drawing.Bitmap]::new($src.Width,$src.Height,[System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
  try{
    $g=[System.Drawing.Graphics]::FromImage($out)
    try{
      $g.Clear([System.Drawing.Color]::FromArgb(255,30,34,36));$g.DrawImageUnscaled($src,0,0)
      $minor=[System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(70,70,210,255),1)
      $major=[System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(190,255,190,40),2)
      $font=[System.Drawing.Font]::new('Arial',14,[System.Drawing.FontStyle]::Bold);$brush=[System.Drawing.SolidBrush]::new([System.Drawing.Color]::White)
      try{for($i=0;$i -lt $src.Width;$i+=50){$p=if(($i%100)-eq 0){$major}else{$minor};$g.DrawLine($p,$i,0,$i,$src.Height);$g.DrawLine($p,0,$i,$src.Width,$i);if(($i%100)-eq 0){$g.DrawString([string]$i,$font,$brush,$i+3,3);$g.DrawString([string]$i,$font,$brush,3,$i+3)}}}
      finally{$minor.Dispose();$major.Dispose();$font.Dispose();$brush.Dispose()}
    }finally{$g.Dispose()}
    $out.Save((Join-Path $PSScriptRoot 'inspect_raw_camel_grid.png'),[System.Drawing.Imaging.ImageFormat]::Png)
  }finally{$out.Dispose()}
}finally{$src.Dispose()}
