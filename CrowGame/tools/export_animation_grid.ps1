$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing

$project=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$source=Join-Path $project 'assets\Character Creation 32P\Character Creation 32P\Animations.png'
$destination=Join-Path $project 'animation_grid_debug.png'
$image=[System.Drawing.Bitmap]::new($source)
try{
    $scale=4;$label=32
    $out=[System.Drawing.Bitmap]::new(($image.Width*$scale)+$label,($image.Height*$scale)+$label)
    try{
        $g=[System.Drawing.Graphics]::FromImage($out)
        try{
            $g.Clear([System.Drawing.Color]::FromArgb(255,24,24,28))
            $g.InterpolationMode=[System.Drawing.Drawing2D.InterpolationMode]::NearestNeighbor
            $g.PixelOffsetMode=[System.Drawing.Drawing2D.PixelOffsetMode]::Half
            $g.DrawImage($image,[System.Drawing.Rectangle]::new($label,$label,$image.Width*$scale,$image.Height*$scale))
            $pen=[System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(150,80,220,255),1)
            $font=[System.Drawing.Font]::new('Consolas',10,[System.Drawing.FontStyle]::Bold)
            $brush=[System.Drawing.Brushes]::White
            try{
                for($column=0;$column -le 9;$column++){
                    $x=$label+(8+$column*32)*$scale
                    $g.DrawLine($pen,$x,$label,$x,$out.Height)
                    if($column -lt 9){$g.DrawString(('c{0}' -f $column),$font,$brush,$x+3,3)}
                }
                for($row=0;$row -le 18;$row++){
                    $y=$label+(8+$row*32)*$scale
                    $g.DrawLine($pen,$label,$y,$out.Width,$y)
                    if($row -lt 18){$g.DrawString(('r{0}' -f $row),$font,$brush,1,$y+3)}
                }
            }finally{$pen.Dispose();$font.Dispose()}
        }finally{$g.Dispose()}
        $out.Save($destination,[System.Drawing.Imaging.ImageFormat]::Png)
    }finally{$out.Dispose()}
}finally{$image.Dispose()}
Write-Output $destination
