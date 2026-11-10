$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$guide = [System.Drawing.Bitmap]::new(1536, 256, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
$graphics = [System.Drawing.Graphics]::FromImage($guide)
try {
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $graphics.Clear([System.Drawing.Color]::FromArgb(255, 22, 25, 29))

    $bodyPen = [System.Drawing.Pen]::new([System.Drawing.Color]::White, 5)
    $nearForePen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(255, 255, 76, 76), 8)
    $farForePen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(255, 255, 174, 55), 7)
    $nearHindPen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(255, 65, 166, 255), 8)
    $farHindPen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(255, 75, 226, 207), 7)
    $groundPen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(255, 105, 115, 125), 2)
    $arrowPen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(255, 180, 255, 120), 4)
    $arrowPen.CustomEndCap = [System.Drawing.Drawing2D.AdjustableArrowCap]::new(6, 8)
    $dividerPen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(255, 65, 72, 80), 2)
    $titleFont = [System.Drawing.Font]::new('Arial', 13, [System.Drawing.FontStyle]::Bold)
    $smallFont = [System.Drawing.Font]::new('Arial', 9, [System.Drawing.FontStyle]::Regular)

    $names = @('LONG CONTACT A', 'PUSH BACK', 'PASS / LIFT', 'LONG CONTACT B', 'PUSH BACK', 'PASS / LIFT')
    $bodyY = @(78, 84, 75, 78, 84, 75)
    $nearForeX = @(218, 192, 150, 112, 132, 178)
    $nearHindX = @(55, 45, 88, 155, 175, 120)
    $farForeX = @(152, 128, 205, 215, 190, 150)
    $farHindX = @(105, 155, 175, 62, 45, 92)
    $liftNearFore = @($false, $false, $true, $false, $false, $true)
    $liftNearHind = @($false, $true, $true, $false, $false, $true)
    $liftFarFore = @($true, $true, $false, $false, $false, $true)
    $liftFarHind = @($true, $false, $false, $true, $true, $false)

    for ($frame = 0; $frame -lt 6; $frame++) {
        $offset = $frame * 256
        if ($frame -gt 0) { $graphics.DrawLine($dividerPen, $offset, 0, $offset, 256) }

        $graphics.DrawString(('F{0} {1}' -f $frame, $names[$frame]), $titleFont, [System.Drawing.Brushes]::White, $offset + 8, 8)
        $graphics.DrawLine($arrowPen, $offset + 165, 35, $offset + 235, 35)
        $graphics.DrawString('EAST / FORWARD', $smallFont, [System.Drawing.Brushes]::LightGreen, $offset + 75, 31)

        $y = $bodyY[$frame]
        $graphics.DrawEllipse($bodyPen, $offset + 58, $y, 122, 58)
        $graphics.DrawEllipse($bodyPen, $offset + 168, $y + 3, 48, 38)
        $graphics.DrawLine($bodyPen, $offset + 206, $y + 21, $offset + 232, $y + 26)
        $graphics.DrawLine($bodyPen, $offset + 61, $y + 17, $offset + 33, $y + 5)
        $graphics.DrawLine($groundPen, $offset + 20, 224, $offset + 238, 224)

        $nearForeStart = [System.Drawing.Point]::new($offset + 166, $y + 45)
        $farForeStart = [System.Drawing.Point]::new($offset + 151, $y + 43)
        $nearHindStart = [System.Drawing.Point]::new($offset + 84, $y + 45)
        $farHindStart = [System.Drawing.Point]::new($offset + 69, $y + 43)

        $nfY = if ($liftNearFore[$frame]) { 198 } else { 220 }
        $ffY = if ($liftFarFore[$frame]) { 199 } else { 212 }
        $nhY = if ($liftNearHind[$frame]) { 197 } else { 220 }
        $fhY = if ($liftFarHind[$frame]) { 198 } else { 212 }

        $nearForeEnd = [System.Drawing.Point]::new($offset + $nearForeX[$frame], $nfY)
        $farForeEnd = [System.Drawing.Point]::new($offset + $farForeX[$frame], $ffY)
        $nearHindEnd = [System.Drawing.Point]::new($offset + $nearHindX[$frame], $nhY)
        $farHindEnd = [System.Drawing.Point]::new($offset + $farHindX[$frame], $fhY)

        foreach ($leg in @(
            @{ Pen = $farForePen; Start = $farForeStart; End = $farForeEnd; KneeY = 161 },
            @{ Pen = $farHindPen; Start = $farHindStart; End = $farHindEnd; KneeY = 158 },
            @{ Pen = $nearForePen; Start = $nearForeStart; End = $nearForeEnd; KneeY = 168 },
            @{ Pen = $nearHindPen; Start = $nearHindStart; End = $nearHindEnd; KneeY = 165 }
        )) {
            $knee = [System.Drawing.Point]::new([int](($leg.Start.X + $leg.End.X) / 2), $leg.KneeY)
            $graphics.DrawLine($leg.Pen, $leg.Start, $knee)
            $graphics.DrawLine($leg.Pen, $knee, $leg.End)
            $graphics.DrawEllipse($leg.Pen, $leg.End.X - 6, $leg.End.Y - 3, 12, 6)
        }

        $graphics.DrawString('red/orange=fore  blue/cyan=hind', $smallFont, [System.Drawing.Brushes]::White, $offset + 8, 238)
    }

    $guide.Save((Join-Path $PSScriptRoot 'ref_e_forward_guide.png'), [System.Drawing.Imaging.ImageFormat]::Png)
}
finally {
    $graphics.Dispose()
    foreach ($resource in @($bodyPen, $nearForePen, $farForePen, $nearHindPen, $farHindPen, $groundPen, $arrowPen, $dividerPen, $titleFont, $smallFont)) {
        if ($resource) { $resource.Dispose() }
    }
    $guide.Dispose()
}
