$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$source = [System.Drawing.Bitmap]::new((Resolve-Path (Join-Path $PSScriptRoot 'whole_sequence_raw.png')).Path)
try {
    if ($source.Width -ne 2172 -or $source.Height -ne 724) { throw "Unexpected sequence size" }

    # Collapse the generator's low-alpha backdrop/halo into transparency before
    # resizing. High-quality downsampling then recreates a clean antialiased edge.
    for ($sourceY = 0; $sourceY -lt $source.Height; $sourceY++) {
        for ($sourceX = 0; $sourceX -lt $source.Width; $sourceX++) {
            $sourceColor = $source.GetPixel($sourceX, $sourceY)
            if ($sourceColor.A -lt 96) {
                $source.SetPixel($sourceX, $sourceY, [System.Drawing.Color]::Transparent)
            }
            else {
                $source.SetPixel($sourceX, $sourceY, [System.Drawing.Color]::FromArgb(255, $sourceColor.R, $sourceColor.G, $sourceColor.B))
            }
        }
    }
    $cellWidth = 362
    $boundsList = @()
    $maximumWidth = 0
    $maximumHeight = 0

    for ($frame = 0; $frame -lt 6; $frame++) {
        $startX = $frame * $cellWidth
        $minX = $startX + $cellWidth; $minY = $source.Height; $maxX = -1; $maxY = -1
        for ($y = 0; $y -lt $source.Height; $y++) {
            for ($x = $startX; $x -lt ($startX + $cellWidth); $x++) {
                if ($source.GetPixel($x, $y).A -ge 64) {
                    if ($x -lt $minX) { $minX = $x }; if ($x -gt $maxX) { $maxX = $x }
                    if ($y -lt $minY) { $minY = $y }; if ($y -gt $maxY) { $maxY = $y }
                }
            }
        }
        if ($maxX -lt 0) { throw "No opaque pixels in frame $frame" }
        $bounds = [System.Drawing.Rectangle]::new($minX, $minY, $maxX - $minX + 1, $maxY - $minY + 1)
        $boundsList += $bounds
        if ($bounds.Width -gt $maximumWidth) { $maximumWidth = $bounds.Width }
        if ($bounds.Height -gt $maximumHeight) { $maximumHeight = $bounds.Height }
    }

    # Shared scales preserve relative stride width, compression, and vertical bob.
    $scaleX = 178.0 / $maximumWidth
    $scaleY = 147.0 / $maximumHeight
    $frames = @()
    for ($frame = 0; $frame -lt 6; $frame++) {
        $bounds = $boundsList[$frame]
        $destinationWidth = [Math]::Max(1, [int][Math]::Round($bounds.Width * $scaleX))
        $destinationHeight = [Math]::Max(1, [int][Math]::Round($bounds.Height * $scaleY))
        $destinationX = [int][Math]::Round(128 - ($destinationWidth / 2.0))
        $destinationY = 248 - $destinationHeight

        $out = [System.Drawing.Bitmap]::new(256, 256, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
        $graphics = [System.Drawing.Graphics]::FromImage($out)
        try {
            $graphics.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceCopy
            $graphics.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
            $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
            $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
            $graphics.Clear([System.Drawing.Color]::Transparent)
            $graphics.DrawImage($source, [System.Drawing.Rectangle]::new($destinationX, $destinationY, $destinationWidth, $destinationHeight), $bounds, [System.Drawing.GraphicsUnit]::Pixel)
        }
        finally { $graphics.Dispose() }

        # Neutralize saturated guide-colored residue in the lower body.
        for ($y = 125; $y -lt 256; $y++) {
            for ($x = 0; $x -lt 256; $x++) {
                $color = $out.GetPixel($x, $y)
                if ($color.A -lt 16) { $out.SetPixel($x, $y, [System.Drawing.Color]::Transparent); continue }
                $maximum = [Math]::Max($color.R, [Math]::Max($color.G, $color.B))
                $minimum = [Math]::Min($color.R, [Math]::Min($color.G, $color.B))
                if (($maximum - $minimum) -gt 55) {
                    $luma = [int](0.30 * $color.R + 0.59 * $color.G + 0.11 * $color.B)
                    $out.SetPixel($x, $y, [System.Drawing.Color]::FromArgb($color.A, [Math]::Min(255, $luma + 5), [Math]::Max(0, $luma - 4), [Math]::Max(0, $luma - 10)))
                }
            }
        }

        [long]$sumR = 0; [long]$sumG = 0; [long]$sumB = 0; [long]$count = 0
        for ($y = 0; $y -lt 256; $y++) { for ($x = 0; $x -lt 256; $x++) {
            $color = $out.GetPixel($x, $y)
            if ($color.A -ge 64) { $sumR += $color.R; $sumG += $color.G; $sumB += $color.B; $count++ }
        }}
        $deltaR = 98 - [int]($sumR / $count); $deltaG = 89 - [int]($sumG / $count); $deltaB = 83 - [int]($sumB / $count)
        for ($y = 0; $y -lt 256; $y++) { for ($x = 0; $x -lt 256; $x++) {
            $color = $out.GetPixel($x, $y)
            if ($color.A -lt 16) { $out.SetPixel($x, $y, [System.Drawing.Color]::Transparent); continue }
            $r = [Math]::Max(0, [Math]::Min(255, $color.R + $deltaR)); $g = [Math]::Max(0, [Math]::Min(255, $color.G + $deltaG)); $b = [Math]::Max(0, [Math]::Min(255, $color.B + $deltaB))
            $out.SetPixel($x, $y, [System.Drawing.Color]::FromArgb($color.A, $r, $g, $b))
        }}

        $out.Save((Join-Path $PSScriptRoot ('sequence_E_{0}.png' -f $frame)), [System.Drawing.Imaging.ImageFormat]::Png)
        $frames += $out
        Write-Output ('frame{0}: source={1},{2},{3},{4} dest={5},{6},{7},{8}' -f $frame, $bounds.X, $bounds.Y, $bounds.Width, $bounds.Height, $destinationX, $destinationY, $destinationWidth, $destinationHeight)
    }

    $preview = [System.Drawing.Bitmap]::new(1536, 256, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    try {
        $graphics = [System.Drawing.Graphics]::FromImage($preview)
        try {
            $graphics.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceCopy
            $graphics.Clear([System.Drawing.Color]::Transparent)
            for ($frame = 0; $frame -lt 6; $frame++) { $graphics.DrawImageUnscaled($frames[$frame], $frame * 256, 0) }
        }
        finally { $graphics.Dispose() }
        $preview.Save((Join-Path $PSScriptRoot 'preview_sequence_E.png'), [System.Drawing.Imaging.ImageFormat]::Png)
    }
    finally { $preview.Dispose() }
    foreach ($frameBitmap in $frames) { $frameBitmap.Dispose() }
}
finally { $source.Dispose() }
