$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$root = $PSScriptRoot
$offsets = @(
    [pscustomobject]@{ Near=240; Far=-240 },
    [pscustomobject]@{ Near=120; Far=-120 },
    [pscustomobject]@{ Near=-80; Far=80 },
    [pscustomobject]@{ Near=-240; Far=240 },
    [pscustomobject]@{ Near=-120; Far=120 },
    [pscustomobject]@{ Near=80; Far=-80 }
)

for ($frame = 0; $frame -lt 6; $frame++) {
    $bitmap = [System.Drawing.Bitmap]::new(1200, 900, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    try {
        $g = [System.Drawing.Graphics]::FromImage($bitmap)
        try {
            $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
            $g.Clear([System.Drawing.Color]::White)
            $bodyBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(220, 225, 225, 225))
            $outline = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(60, 60, 60), 12)
            $nearPen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(220, 25, 45), 34)
            $farPen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(30, 90, 220), 26)
            $nearBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(220, 25, 45))
            $farBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(30, 90, 220))
            $font = [System.Drawing.Font]::new('Arial', 30, [System.Drawing.FontStyle]::Bold)
            $textBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::Black)
            try {
                $g.FillEllipse($bodyBrush, 250, 250, 610, 310)
                $g.DrawEllipse($outline, 250, 250, 610, 310)
                $g.FillEllipse($bodyBrush, 800, 280, 250, 210)
                $g.DrawEllipse($outline, 800, 280, 250, 210)
                $g.DrawLine($outline, 270, 355, 110, 455)

                $hindX = 380
                $foreX = 740
                $jointY = 505
                $pawY = 780
                $nearHindX = $hindX + $offsets[$frame].Near
                $nearForeX = $foreX + $offsets[$frame].Near
                $farHindX = $hindX + $offsets[$frame].Far
                $farForeX = $foreX + $offsets[$frame].Far

                $g.DrawLine($farPen, $hindX, $jointY, $farHindX, $pawY)
                $g.DrawLine($farPen, $foreX, $jointY, $farForeX, $pawY)
                $g.FillEllipse($farBrush, $farHindX - 28, $pawY - 22, 56, 44)
                $g.FillEllipse($farBrush, $farForeX - 28, $pawY - 22, 56, 44)
                $g.DrawLine($nearPen, $hindX, $jointY, $nearHindX, $pawY)
                $g.DrawLine($nearPen, $foreX, $jointY, $nearForeX, $pawY)
                $g.FillEllipse($nearBrush, $nearHindX - 34, $pawY - 26, 68, 52)
                $g.FillEllipse($nearBrush, $nearForeX - 34, $pawY - 26, 68, 52)

                $g.DrawString(('E pace frame {0}: RED near-side fore+hind stay paired; BLUE far-side fore+hind stay paired' -f $frame), $font, $textBrush, 35, 35)
            }
            finally {
                $bodyBrush.Dispose(); $outline.Dispose(); $nearPen.Dispose(); $farPen.Dispose()
                $nearBrush.Dispose(); $farBrush.Dispose(); $font.Dispose(); $textBrush.Dispose()
            }
        }
        finally { $g.Dispose() }
        $bitmap.Save((Join-Path $root ('guide_E_{0}.png' -f $frame)), [System.Drawing.Imaging.ImageFormat]::Png)
    }
    finally { $bitmap.Dispose() }
}
