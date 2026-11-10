$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

if (-not ('WolfSpritePixelPrep' -as [type])) {
    Add-Type -ReferencedAssemblies @(
        [System.Drawing.Bitmap].Assembly.Location,
        [System.Drawing.Rectangle].Assembly.Location
    ) -TypeDefinition @'
using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;

public static class WolfSpritePixelPrep
{
    public static Rectangle CleanAndGetBounds(Bitmap bitmap, byte alphaThreshold)
    {
        Rectangle rect = new Rectangle(0, 0, bitmap.Width, bitmap.Height);
        BitmapData data = bitmap.LockBits(rect, ImageLockMode.ReadWrite, PixelFormat.Format32bppArgb);
        try
        {
            int absStride = Math.Abs(data.Stride);
            byte[] pixels = new byte[absStride * bitmap.Height];
            Marshal.Copy(data.Scan0, pixels, 0, pixels.Length);
            int minX = bitmap.Width, minY = bitmap.Height, maxX = -1, maxY = -1;
            for (int y = 0; y < bitmap.Height; y++)
            {
                int row = data.Stride >= 0 ? y * data.Stride : (bitmap.Height - 1 - y) * absStride;
                for (int x = 0; x < bitmap.Width; x++)
                {
                    int offset = row + x * 4;
                    if (pixels[offset + 3] < alphaThreshold)
                    {
                        pixels[offset] = pixels[offset + 1] = pixels[offset + 2] = pixels[offset + 3] = 0;
                    }
                    else
                    {
                        pixels[offset + 3] = 255;
                        if (x < minX) minX = x; if (x > maxX) maxX = x;
                        if (y < minY) minY = y; if (y > maxY) maxY = y;
                    }
                }
            }
            Marshal.Copy(pixels, 0, data.Scan0, pixels.Length);
            if (maxX < 0) return Rectangle.Empty;
            return new Rectangle(minX, minY, maxX - minX + 1, maxY - minY + 1);
        }
        finally { bitmap.UnlockBits(data); }
    }
}
'@
}

$sources = @()
$boundsList = @()
$maximumWidth = 0
$maximumHeight = 0

# Normalize small generator camera-zoom differences around the in-game pivot.
# Values come from opaque upper-body mass, not stride bbox, so leg extension is preserved.
$zoomFactors = @(1.008224, 1.012474, 0.965462, 1.043054, 1.009810, 0.987875)

try {
    for ($frame = 0; $frame -lt 6; $frame++) {
        $path = Resolve-Path (Join-Path $PSScriptRoot ('individual_F{0}_raw.png' -f $frame))
        $bitmap = [System.Drawing.Bitmap]::new($path.Path)
        if ($bitmap.Width -ne 1536 -or $bitmap.Height -ne 1024) {
            $bitmap.Dispose()
            throw "Unexpected raw frame size: $frame"
        }

        # Remove the low-alpha studio backdrop and find bounds in one native-speed pass.
        $bounds = [WolfSpritePixelPrep]::CleanAndGetBounds($bitmap, 96)
        if ($bounds.IsEmpty) { $bitmap.Dispose(); throw "No wolf pixels in frame $frame" }
        $sources += $bitmap
        $boundsList += $bounds
        if ($bounds.Width -gt $maximumWidth) { $maximumWidth = $bounds.Width }
        if ($bounds.Height -gt $maximumHeight) { $maximumHeight = $bounds.Height }
    }

    $scaleX = 178.0 / $maximumWidth
    $scaleY = 147.0 / $maximumHeight
    $frames = @()

    for ($frame = 0; $frame -lt 6; $frame++) {
        $source = $sources[$frame]
        $bounds = $boundsList[$frame]
        $zoom = $zoomFactors[$frame]
        $width = [Math]::Max(1, [int][Math]::Round($bounds.Width * $scaleX * $zoom))
        $height = [Math]::Max(1, [int][Math]::Round($bounds.Height * $scaleY * $zoom))
        $destinationX = [int][Math]::Round(128 - ($width / 2.0))
        $destinationY = 248 - $height

        $out = [System.Drawing.Bitmap]::new(256, 256, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
        $graphics = [System.Drawing.Graphics]::FromImage($out)
        try {
            $graphics.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceCopy
            $graphics.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
            $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
            $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
            $graphics.Clear([System.Drawing.Color]::Transparent)
            $graphics.DrawImage($source, [System.Drawing.Rectangle]::new($destinationX, $destinationY, $width, $height), $bounds, [System.Drawing.GraphicsUnit]::Pixel)
        }
        finally { $graphics.Dispose() }

        # Remove any saturated generator residue from legs and floor-adjacent edges.
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
        Write-Output ('frame{0}: raw={1},{2},{3},{4} dest={5},{6},{7},{8}' -f $frame, $bounds.X, $bounds.Y, $bounds.Width, $bounds.Height, $destinationX, $destinationY, $width, $height)
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
finally {
    foreach ($source in $sources) { if ($source) { $source.Dispose() } }
}
