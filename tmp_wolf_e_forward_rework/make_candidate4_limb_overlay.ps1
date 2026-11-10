$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$sourcePath = Resolve-Path (Join-Path $PSScriptRoot 'individual_F4_candidate4_raw.png')
$outputPath = Join-Path $PSScriptRoot 'ref_candidate4_limb_ownership_overlay.png'
$source = [System.Drawing.Bitmap]::new($sourcePath.Path)
$canvas = [System.Drawing.Bitmap]::new($source.Width, $source.Height, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
$graphics = [System.Drawing.Graphics]::FromImage($canvas)

try {
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $graphics.DrawImageUnscaled($source, 0, 0)
    $nearPen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(220, 255, 35, 50), 26)
    $farPen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(220, 25, 145, 255), 22)
    foreach ($pen in @($nearPen, $farPen)) {
        $pen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
        $pen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
    }

    # Foreground LEFT pair: both forward/airborne.
    $graphics.DrawLines($nearPen, [System.Drawing.Point[]]@(
        [System.Drawing.Point]::new(1045, 420),
        [System.Drawing.Point]::new(1080, 555),
        [System.Drawing.Point]::new(1165, 660),
        [System.Drawing.Point]::new(1250, 735)
    ))
    $graphics.DrawLines($nearPen, [System.Drawing.Point[]]@(
        [System.Drawing.Point]::new(610, 420),
        [System.Drawing.Point]::new(600, 550),
        [System.Drawing.Point]::new(640, 680),
        [System.Drawing.Point]::new(710, 755)
    ))

    # Background RIGHT pair: both backward/grounded.
    $graphics.DrawLines($farPen, [System.Drawing.Point[]]@(
        [System.Drawing.Point]::new(970, 470),
        [System.Drawing.Point]::new(925, 620),
        [System.Drawing.Point]::new(875, 770),
        [System.Drawing.Point]::new(890, 845)
    ))
    $graphics.DrawLines($farPen, [System.Drawing.Point[]]@(
        [System.Drawing.Point]::new(540, 465),
        [System.Drawing.Point]::new(420, 575),
        [System.Drawing.Point]::new(270, 745),
        [System.Drawing.Point]::new(205, 845)
    ))

    $font = [System.Drawing.Font]::new('Arial', 27, [System.Drawing.FontStyle]::Bold)
    $graphics.DrawString('RED NEAR LEFT PAIR = BOTH FORWARD + AIRBORNE', $font, [System.Drawing.Brushes]::Red, 35, 28)
    $graphics.DrawString('BLUE FAR RIGHT PAIR = BOTH BACKWARD + GROUNDED', $font, [System.Drawing.Brushes]::DeepSkyBlue, 35, 68)
    $graphics.DrawString('KEEP ROOT-TO-PAW OWNERSHIP; REDRAW THE WHOLE BODY', $font, [System.Drawing.Brushes]::LimeGreen, 35, 108)

    $nearPen.Dispose(); $farPen.Dispose(); $font.Dispose()
    $canvas.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png)
}
finally {
    $graphics.Dispose(); $canvas.Dispose(); $source.Dispose()
}

Write-Output $outputPath
