$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$guide = [System.Drawing.Bitmap]::new(1536, 256, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
$graphics = [System.Drawing.Graphics]::FromImage($guide)
try {
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $graphics.Clear([System.Drawing.Color]::FromArgb(255, 22, 25, 29))

    $bodyPen = [System.Drawing.Pen]::new([System.Drawing.Color]::White, 5)
    $leftPen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(255, 255, 74, 74), 8)
    $rightPen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(255, 65, 170, 255), 7)
    $groundPen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(255, 105, 115, 125), 2)
    $arrowPen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(255, 180, 255, 120), 4)
    $arrowPen.CustomEndCap = [System.Drawing.Drawing2D.AdjustableArrowCap]::new(6, 8)
    $dividerPen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(255, 65, 72, 80), 2)
    $titleFont = [System.Drawing.Font]::new('Arial', 12, [System.Drawing.FontStyle]::Bold)
    $smallFont = [System.Drawing.Font]::new('Arial', 9, [System.Drawing.FontStyle]::Regular)

    $names = @('LEFT PAIR FORWARD', 'LEFT PUSH / RIGHT LIFT', 'RIGHT SWING FORWARD', 'RIGHT PAIR FORWARD', 'RIGHT PUSH / LEFT LIFT', 'LEFT SWING FORWARD')
    $bodyY = @(79, 86, 75, 79, 86, 75)

    # Same-side fore and hind paws share the same phase.
    $leftForeX = @(220, 188, 145, 140, 178, 208)
    $leftHindX = @(128, 105, 55, 50, 92, 125)
    $rightForeX = @(140, 178, 208, 220, 188, 145)
    $rightHindX = @(50, 92, 125, 128, 105, 55)
    $leftLift = @($false, $false, $false, $false, $true, $true)
    $rightLift = @($false, $true, $true, $false, $false, $false)

    for ($frame = 0; $frame -lt 6; $frame++) {
        $offset = $frame * 256
        if ($frame -gt 0) { $graphics.DrawLine($dividerPen, $offset, 0, $offset, 256) }
        $graphics.DrawString(('F{0} {1}' -f $frame, $names[$frame]), $titleFont, [System.Drawing.Brushes]::White, $offset + 7, 7)
        $graphics.DrawLine($arrowPen, $offset + 170, 34, $offset + 237, 34)
        $graphics.DrawString('EAST', $smallFont, [System.Drawing.Brushes]::LightGreen, $offset + 133, 29)
        $graphics.DrawString('RED = LEFT fore+hind pair', $smallFont, [System.Drawing.Brushes]::LightCoral, $offset + 7, 35)
        $graphics.DrawString('BLUE = RIGHT fore+hind pair', $smallFont, [System.Drawing.Brushes]::LightSkyBlue, $offset + 7, 48)

        $y = $bodyY[$frame]
        $graphics.DrawEllipse($bodyPen, $offset + 58, $y, 122, 58)
        $graphics.DrawEllipse($bodyPen, $offset + 168, $y + 3, 48, 38)
        $graphics.DrawLine($bodyPen, $offset + 206, $y + 21, $offset + 232, $y + 26)
        $graphics.DrawLine($bodyPen, $offset + 61, $y + 17, $offset + 33, $y + 5)
        $graphics.DrawLine($groundPen, $offset + 18, 224, $offset + 240, 224)

        $leftForeStart = [System.Drawing.Point]::new($offset + 166, $y + 45)
        $leftHindStart = [System.Drawing.Point]::new($offset + 84, $y + 45)
        $rightForeStart = [System.Drawing.Point]::new($offset + 151, $y + 42)
        $rightHindStart = [System.Drawing.Point]::new($offset + 69, $y + 42)

        $leftY = if ($leftLift[$frame]) { 196 } else { 220 }
        $rightY = if ($rightLift[$frame]) { 196 } else { 212 }
        $legs = @(
            @{ Pen = $rightPen; Start = $rightForeStart; End = [System.Drawing.Point]::new($offset + $rightForeX[$frame], $rightY); Knee = 158 },
            @{ Pen = $rightPen; Start = $rightHindStart; End = [System.Drawing.Point]::new($offset + $rightHindX[$frame], $rightY); Knee = 156 },
            @{ Pen = $leftPen; Start = $leftForeStart; End = [System.Drawing.Point]::new($offset + $leftForeX[$frame], $leftY); Knee = 168 },
            @{ Pen = $leftPen; Start = $leftHindStart; End = [System.Drawing.Point]::new($offset + $leftHindX[$frame], $leftY); Knee = 165 }
        )
        foreach ($leg in $legs) {
            $knee = [System.Drawing.Point]::new([int](($leg.Start.X + $leg.End.X) / 2), $leg.Knee)
            $graphics.DrawLine($leg.Pen, $leg.Start, $knee)
            $graphics.DrawLine($leg.Pen, $knee, $leg.End)
            $graphics.DrawEllipse($leg.Pen, $leg.End.X - 6, $leg.End.Y - 3, 12, 6)
        }
    }

    $guide.Save((Join-Path $PSScriptRoot 'ref_e_pace_guide.png'), [System.Drawing.Imaging.ImageFormat]::Png)
}
finally {
    $graphics.Dispose()
    foreach ($resource in @($bodyPen, $leftPen, $rightPen, $groundPen, $arrowPen, $dividerPen, $titleFont, $smallFont)) {
        if ($resource) { $resource.Dispose() }
    }
    $guide.Dispose()
}
