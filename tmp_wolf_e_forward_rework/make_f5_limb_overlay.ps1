$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$sourcePath = Resolve-Path (Join-Path $PSScriptRoot 'individual_F5_raw.png')
$outputPath = Join-Path $PSScriptRoot 'ref_f5_limb_ownership_overlay.png'

$source = [System.Drawing.Bitmap]::new($sourcePath.Path)
$canvas = [System.Drawing.Bitmap]::new($source.Width, $source.Height, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
$graphics = [System.Drawing.Graphics]::FromImage($canvas)

try {
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $graphics.DrawImageUnscaled($source, 0, 0)

    $nearPen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(215, 255, 40, 55), 26)
    $farPen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(215, 30, 145, 255), 22)
    $nearPen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
    $nearPen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
    $farPen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
    $farPen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round

    # Camera-near LEFT pair: both forward and airborne in the approved F5.
    $graphics.DrawLines($nearPen, [System.Drawing.Point[]]@(
        [System.Drawing.Point]::new(1050, 430),
        [System.Drawing.Point]::new(1105, 555),
        [System.Drawing.Point]::new(1210, 675),
        [System.Drawing.Point]::new(1310, 745)
    ))
    $graphics.DrawLines($nearPen, [System.Drawing.Point[]]@(
        [System.Drawing.Point]::new(610, 435),
        [System.Drawing.Point]::new(625, 565),
        [System.Drawing.Point]::new(695, 680),
        [System.Drawing.Point]::new(785, 755)
    ))

    # Camera-far RIGHT pair: both backward and grounded in the approved F5.
    $graphics.DrawLines($farPen, [System.Drawing.Point[]]@(
        [System.Drawing.Point]::new(980, 465),
        [System.Drawing.Point]::new(925, 600),
        [System.Drawing.Point]::new(885, 760),
        [System.Drawing.Point]::new(915, 840)
    ))
    $graphics.DrawLines($farPen, [System.Drawing.Point[]]@(
        [System.Drawing.Point]::new(545, 480),
        [System.Drawing.Point]::new(430, 565),
        [System.Drawing.Point]::new(275, 745),
        [System.Drawing.Point]::new(205, 840)
    ))

    $font = [System.Drawing.Font]::new('Arial', 28, [System.Drawing.FontStyle]::Bold)
    $graphics.DrawString('RED = NEAR LEFT FORE + LEFT HIND: BOTH FORWARD / AIRBORNE', $font, [System.Drawing.Brushes]::Red, 35, 30)
    $graphics.DrawString('BLUE = FAR RIGHT FORE + RIGHT HIND: BOTH BACKWARD / GROUNDED', $font, [System.Drawing.Brushes]::DeepSkyBlue, 35, 70)

    $nearPen.Dispose()
    $farPen.Dispose()
    $font.Dispose()
    $canvas.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png)
}
finally {
    $graphics.Dispose()
    $canvas.Dispose()
    $source.Dispose()
}

Write-Output $outputPath
