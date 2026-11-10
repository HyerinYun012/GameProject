$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$guide = [System.Drawing.Bitmap]::new(1536, 256, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
$graphics = [System.Drawing.Graphics]::FromImage($guide)
try {
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $graphics.Clear([System.Drawing.Color]::FromArgb(255, 24, 27, 31))

    $bodyPen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(255, 235, 235, 235), 5)
    $nearPen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(255, 255, 72, 72), 8)
    $farPen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(255, 68, 196, 255), 8)
    $groundPen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(255, 115, 125, 135), 2)
    $dividerPen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(255, 70, 76, 84), 2)
    $font = [System.Drawing.Font]::new('Arial', 14, [System.Drawing.FontStyle]::Bold)
    $smallFont = [System.Drawing.Font]::new('Arial', 10, [System.Drawing.FontStyle]::Regular)
    $white = [System.Drawing.Brushes]::White
    $nearBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(255, 255, 100, 100))
    $farBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(255, 105, 205, 255))

    $phase = @(1.0, 0.45, -0.35, -1.0, -0.45, 0.35)
    $names = @('CONTACT A', 'DOWN A', 'PASS TO B', 'CONTACT B', 'DOWN B', 'PASS TO A')

    for ($frame = 0; $frame -lt 6; $frame++) {
        $offsetX = $frame * 256
        if ($frame -gt 0) {
            $graphics.DrawLine($dividerPen, $offsetX, 0, $offsetX, 256)
        }

        $graphics.DrawString(('F{0}' -f $frame), $font, $white, $offsetX + 10, 8)
        $graphics.DrawString($names[$frame], $smallFont, $white, $offsetX + 42, 12)
        $graphics.DrawString('RED = near/right pair', $smallFont, $nearBrush, $offsetX + 10, 35)
        $graphics.DrawString('BLUE = far/left pair', $smallFont, $farBrush, $offsetX + 10, 50)

        $graphics.DrawEllipse($bodyPen, $offsetX + 62, 73, 116, 62)
        $graphics.DrawEllipse($bodyPen, $offsetX + 164, 72, 48, 42)
        $graphics.DrawLine($bodyPen, $offsetX + 202, 96, $offsetX + 225, 112)
        $graphics.DrawLine($bodyPen, $offsetX + 65, 96, $offsetX + 40, 78)
        $graphics.DrawLine($groundPen, $offsetX + 20, 220, $offsetX + 236, 220)

        $p = [double]$phase[$frame]
        $nearShift = [int](38 * $p)
        $farShift = -$nearShift

        $nearShoulder = [System.Drawing.Point]::new($offsetX + 164, 120)
        $nearHip = [System.Drawing.Point]::new($offsetX + 85, 122)
        $farShoulder = [System.Drawing.Point]::new($offsetX + 148, 112)
        $farHip = [System.Drawing.Point]::new($offsetX + 70, 112)

        $nearFrontPaw = [System.Drawing.Point]::new($offsetX + 165 + $nearShift, 215)
        $nearHindPaw = [System.Drawing.Point]::new($offsetX + 86 + $nearShift, 215)
        $farFrontPaw = [System.Drawing.Point]::new($offsetX + 148 + $farShift, 202)
        $farHindPaw = [System.Drawing.Point]::new($offsetX + 69 + $farShift, 202)

        $graphics.DrawLine($farPen, $farShoulder, [System.Drawing.Point]::new(($farShoulder.X + $farFrontPaw.X) / 2, 158))
        $graphics.DrawLine($farPen, [System.Drawing.Point]::new(($farShoulder.X + $farFrontPaw.X) / 2, 158), $farFrontPaw)
        $graphics.DrawLine($farPen, $farHip, [System.Drawing.Point]::new(($farHip.X + $farHindPaw.X) / 2, 158))
        $graphics.DrawLine($farPen, [System.Drawing.Point]::new(($farHip.X + $farHindPaw.X) / 2, 158), $farHindPaw)

        $graphics.DrawLine($nearPen, $nearShoulder, [System.Drawing.Point]::new(($nearShoulder.X + $nearFrontPaw.X) / 2, 166))
        $graphics.DrawLine($nearPen, [System.Drawing.Point]::new(($nearShoulder.X + $nearFrontPaw.X) / 2, 166), $nearFrontPaw)
        $graphics.DrawLine($nearPen, $nearHip, [System.Drawing.Point]::new(($nearHip.X + $nearHindPaw.X) / 2, 166))
        $graphics.DrawLine($nearPen, [System.Drawing.Point]::new(($nearHip.X + $nearHindPaw.X) / 2, 166), $nearHindPaw)

        $graphics.FillEllipse($farBrush, $farFrontPaw.X - 6, $farFrontPaw.Y - 4, 12, 8)
        $graphics.FillEllipse($farBrush, $farHindPaw.X - 6, $farHindPaw.Y - 4, 12, 8)
        $graphics.FillEllipse($nearBrush, $nearFrontPaw.X - 7, $nearFrontPaw.Y - 5, 14, 10)
        $graphics.FillEllipse($nearBrush, $nearHindPaw.X - 7, $nearHindPaw.Y - 5, 14, 10)
    }

    $guide.Save((Join-Path $PSScriptRoot 'ref_motion_guide.png'), [System.Drawing.Imaging.ImageFormat]::Png)
}
finally {
    $graphics.Dispose()
    if ($bodyPen) { $bodyPen.Dispose() }
    if ($nearPen) { $nearPen.Dispose() }
    if ($farPen) { $farPen.Dispose() }
    if ($groundPen) { $groundPen.Dispose() }
    if ($dividerPen) { $dividerPen.Dispose() }
    if ($font) { $font.Dispose() }
    if ($smallFont) { $smallFont.Dispose() }
    if ($nearBrush) { $nearBrush.Dispose() }
    if ($farBrush) { $farBrush.Dispose() }
    $guide.Dispose()
}
