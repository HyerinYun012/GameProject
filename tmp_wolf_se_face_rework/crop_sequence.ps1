$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$source = [System.Drawing.Bitmap]::new((Resolve-Path (Join-Path $PSScriptRoot 'whole_sequence_raw.png')).Path)
try {
    if ($source.Width -ne 2172 -or $source.Height -ne 724) {
        throw "Unexpected sequence size: $($source.Width)x$($source.Height)"
    }

    $cellWidth = 362
    $frames = @()

    for ($frame = 0; $frame -lt 6; $frame++) {
        $startX = $frame * $cellWidth
        $minX = $startX + $cellWidth
        $minY = $source.Height
        $maxX = -1
        $maxY = -1

        for ($y = 0; $y -lt $source.Height; $y++) {
            for ($x = $startX; $x -lt ($startX + $cellWidth); $x++) {
                if ($source.GetPixel($x, $y).A -ge 64) {
                    if ($x -lt $minX) { $minX = $x }
                    if ($x -gt $maxX) { $maxX = $x }
                    if ($y -lt $minY) { $minY = $y }
                    if ($y -gt $maxY) { $maxY = $y }
                }
            }
        }

        if ($maxX -lt 0) { throw "No opaque pixels in frame $frame" }

        $bounds = [System.Drawing.Rectangle]::new(
            $minX,
            $minY,
            $maxX - $minX + 1,
            $maxY - $minY + 1
        )

        $out = [System.Drawing.Bitmap]::new(256, 256, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
        $graphics = [System.Drawing.Graphics]::FromImage($out)
        try {
            $graphics.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceCopy
            $graphics.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
            $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
            $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
            $graphics.Clear([System.Drawing.Color]::Transparent)
            $graphics.DrawImage(
                $source,
                [System.Drawing.Rectangle]::new(64, 88, 128, 160),
                $bounds,
                [System.Drawing.GraphicsUnit]::Pixel
            )
        }
        finally {
            $graphics.Dispose()
        }

        [long]$sumR = 0
        [long]$sumG = 0
        [long]$sumB = 0
        [long]$count = 0
        for ($y = 0; $y -lt 256; $y++) {
            for ($x = 0; $x -lt 256; $x++) {
                $color = $out.GetPixel($x, $y)
                if ($color.A -ge 64) {
                    $sumR += $color.R
                    $sumG += $color.G
                    $sumB += $color.B
                    $count++
                }
            }
        }

        $deltaR = 97 - [int]($sumR / $count)
        $deltaG = 88 - [int]($sumG / $count)
        $deltaB = 82 - [int]($sumB / $count)

        for ($y = 0; $y -lt 256; $y++) {
            for ($x = 0; $x -lt 256; $x++) {
                $color = $out.GetPixel($x, $y)
                if ($color.A -lt 16) {
                    $out.SetPixel($x, $y, [System.Drawing.Color]::Transparent)
                    continue
                }

                $r = [Math]::Max(0, [Math]::Min(255, $color.R + $deltaR))
                $g = [Math]::Max(0, [Math]::Min(255, $color.G + $deltaG))
                $b = [Math]::Max(0, [Math]::Min(255, $color.B + $deltaB))
                $out.SetPixel($x, $y, [System.Drawing.Color]::FromArgb($color.A, $r, $g, $b))
            }
        }

        $out.Save(
            (Join-Path $PSScriptRoot ('sequence_SE_{0}.png' -f $frame)),
            [System.Drawing.Imaging.ImageFormat]::Png
        )
        $frames += $out
        Write-Output ('frame{0}: source={1},{2},{3},{4}' -f $frame, $bounds.X, $bounds.Y, $bounds.Width, $bounds.Height)
    }

    $preview = [System.Drawing.Bitmap]::new(1536, 256, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    try {
        $graphics = [System.Drawing.Graphics]::FromImage($preview)
        try {
            $graphics.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceCopy
            $graphics.Clear([System.Drawing.Color]::Transparent)
            for ($frame = 0; $frame -lt 6; $frame++) {
                $graphics.DrawImageUnscaled($frames[$frame], $frame * 256, 0)
            }
        }
        finally {
            $graphics.Dispose()
        }
        $preview.Save((Join-Path $PSScriptRoot 'preview_sequence_SE.png'), [System.Drawing.Imaging.ImageFormat]::Png)
    }
    finally {
        $preview.Dispose()
    }

    foreach ($frameBitmap in $frames) { $frameBitmap.Dispose() }
}
finally {
    $source.Dispose()
}
