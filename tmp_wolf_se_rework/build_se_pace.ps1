$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$sourcePath = (Resolve-Path (Join-Path $PSScriptRoot '..\tmp_wolf_work\styled_SE_0.png')).Path
$workSize = 1024
$scale = 4.0

function New-TransparentBitmap([int]$Width, [int]$Height) {
    $bitmap = [System.Drawing.Bitmap]::new($Width, $Height, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    try {
        $graphics.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceCopy
        $graphics.Clear([System.Drawing.Color]::Transparent)
    }
    finally { $graphics.Dispose() }
    return $bitmap
}

function Convert-Points([object[]]$Coordinates) {
    $points = [System.Drawing.PointF[]]::new($Coordinates.Count)
    for ($i = 0; $i -lt $Coordinates.Count; $i++) {
        $points[$i] = [System.Drawing.PointF]::new([single]($Coordinates[$i][0] * $scale), [single]($Coordinates[$i][1] * $scale))
    }
    return $points
}

function New-MaskedLayer([System.Drawing.Bitmap]$Source, [object[]]$Coordinates) {
    $layer = New-TransparentBitmap $workSize $workSize
    $graphics = [System.Drawing.Graphics]::FromImage($layer)
    try {
        $graphics.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceCopy
        $graphics.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
        $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
        $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
        $path = [System.Drawing.Drawing2D.GraphicsPath]::new()
        try {
            [System.Drawing.PointF[]]$maskPoints = Convert-Points $Coordinates
            $path.AddPolygon($maskPoints)
            $graphics.SetClip($path)
            $graphics.DrawImage($Source, [System.Drawing.Rectangle]::new(0, 0, $workSize, $workSize), [System.Drawing.Rectangle]::new(0, 0, 256, 256), [System.Drawing.GraphicsUnit]::Pixel)
        }
        finally { $path.Dispose() }
    }
    finally { $graphics.Dispose() }
    return $layer
}

function Draw-TransformedLayer {
    param(
        [System.Drawing.Graphics]$Graphics,
        [System.Drawing.Bitmap]$Layer,
        [double]$PivotX,
        [double]$PivotY,
        [double]$Angle,
        [double]$LengthScale,
        [double]$LiftY
    )
    $state = $Graphics.Save()
    try {
        $px = [single]($PivotX * $scale)
        $py = [single](($PivotY + $LiftY) * $scale)
        $Graphics.TranslateTransform($px, $py)
        $Graphics.RotateTransform([single]$Angle)
        $Graphics.ScaleTransform([single]$LengthScale, [single]$LengthScale)
        $Graphics.TranslateTransform(-[single]($PivotX * $scale), -[single]($PivotY * $scale))
        $Graphics.DrawImageUnscaled($Layer, 0, 0)
    }
    finally { $Graphics.Restore($state) }
}

function Get-AlphaBounds([System.Drawing.Bitmap]$Bitmap, [int]$Threshold = 16) {
    $minX = $Bitmap.Width; $minY = $Bitmap.Height; $maxX = -1; $maxY = -1
    for ($y = 0; $y -lt $Bitmap.Height; $y++) {
        for ($x = 0; $x -lt $Bitmap.Width; $x++) {
            if ($Bitmap.GetPixel($x, $y).A -ge $Threshold) {
                if ($x -lt $minX) { $minX = $x }
                if ($x -gt $maxX) { $maxX = $x }
                if ($y -lt $minY) { $minY = $y }
                if ($y -gt $maxY) { $maxY = $y }
            }
        }
    }
    if ($maxX -lt 0) { throw 'No visible pixels in frame.' }
    return [System.Drawing.Rectangle]::new($minX, $minY, $maxX - $minX + 1, $maxY - $minY + 1)
}

$source = [System.Drawing.Bitmap]::new($sourcePath)
try {
    # Source frame anatomy at 256x256.  These masks preserve the established
    # texture while letting each physical leg retain a fixed depth identity.
    $farHind = New-MaskedLayer $source @(
        @(68,143), @(96,143), @(99,158), @(96,176), @(92,193), @(78,196), @(68,188), @(72,166)
    )
    $nearHind = New-MaskedLayer $source @(
        @(94,147), @(120,149), @(124,166), @(123,188), @(128,205), @(121,219), @(107,220), @(98,210), @(100,182)
    )
    $farFore = New-MaskedLayer $source @(
        @(118,153), @(151,153), @(153,169), @(150,188), @(151,206), @(143,216), @(129,214), @(122,205), @(125,180)
    )
    $nearFore = New-MaskedLayer $source @(
        @(145,151), @(173,153), @(180,177), @(182,203), @(188,224), @(182,241), @(165,242), @(156,231), @(157,198), @(150,174)
    )
    $body = New-MaskedLayer $source @(
        @(62,116), @(68,98), @(84,83), @(101,76), @(124,82), @(143,96), @(158,108), @(174,112),
        @(187,125), @(194,145), @(193,165), @(187,180), @(176,188), @(158,187), @(145,178),
        @(134,169), @(119,166), @(104,163), @(88,160), @(72,156), @(62,145)
    )

    try {
        $phase = @(0.00, 0.34, 0.68, 1.00, 0.68, 0.34)
        $farLift = @(0.0, -3.0, -5.0, 0.0, 0.0, 0.0)
        $nearLift = @(0.0, 0.0, 0.0, 0.0, -3.0, -5.0)
        $preview = New-TransparentBitmap 1536 256
        try {
            $previewGraphics = [System.Drawing.Graphics]::FromImage($preview)
            try {
                $previewGraphics.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceOver
                $previewGraphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::NearestNeighbor

                for ($frame = 0; $frame -lt 6; $frame++) {
                    $t = $phase[$frame]
                    $hires = New-TransparentBitmap $workSize $workSize
                    try {
                        $g = [System.Drawing.Graphics]::FromImage($hires)
                        try {
                            $g.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceOver
                            $g.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
                            $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
                            $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
                            $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality

                            # LEFT/FAR fore + hind are one locked phase group and
                            # advance together while the right/near group retreats.
                            Draw-TransformedLayer $g $farHind 91 151 (-45.0 * $t) (1.0 + 0.78 * $t) $farLift[$frame]
                            Draw-TransformedLayer $g $farFore 141 158 (-43.0 * $t) (1.0 + 0.62 * $t) $farLift[$frame]

                            # Body/head/tail remain fixed so direction and identity
                            # cannot drift between frames.
                            $g.DrawImageUnscaled($body, 0, 0)

                            # RIGHT/NEAR fore + hind are the opposing locked group.
                            Draw-TransformedLayer $g $nearHind 108 154 (35.0 * $t) (1.0 + 0.15 * $t) $nearLift[$frame]
                            Draw-TransformedLayer $g $nearFore 159 159 (45.0 * $t) (1.0 + 0.30 * $t) $nearLift[$frame]
                        }
                        finally { $g.Dispose() }

                        $frameBitmap = New-TransparentBitmap 256 256
                        try {
                            $down = [System.Drawing.Graphics]::FromImage($frameBitmap)
                            try {
                                $down.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceCopy
                                $down.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
                                $down.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
                                $down.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
                                $down.DrawImage($hires, [System.Drawing.Rectangle]::new(0, 0, 256, 256), [System.Drawing.Rectangle]::new(0, 0, $workSize, $workSize), [System.Drawing.GraphicsUnit]::Pixel)
                            }
                            finally { $down.Dispose() }

                            # The body pivot is fixed across the animation.  The
                            # original source was 10px above the project's floor,
                            # so apply exactly one constant correction to all frames.
                            $shiftY = 10
                            if ($shiftY -ne 0) {
                                $anchored = New-TransparentBitmap 256 256
                                try {
                                    $anchorGraphics = [System.Drawing.Graphics]::FromImage($anchored)
                                    try {
                                        $anchorGraphics.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceCopy
                                        $anchorGraphics.DrawImageUnscaled($frameBitmap, 0, $shiftY)
                                    }
                                    finally { $anchorGraphics.Dispose() }
                                    $frameBitmap.Dispose()
                                    $frameBitmap = $anchored
                                    $anchored = $null
                                }
                                finally { if ($null -ne $anchored) { $anchored.Dispose() } }
                            }

                            # Remove barely-visible resampling halo pixels.
                            for ($y = 0; $y -lt 256; $y++) {
                                for ($x = 0; $x -lt 256; $x++) {
                                    $c = $frameBitmap.GetPixel($x, $y)
                                    if ($c.A -lt 16) { $frameBitmap.SetPixel($x, $y, [System.Drawing.Color]::Transparent) }
                                }
                            }

                            $outPath = Join-Path $PSScriptRoot ('pace_SE_{0}.png' -f $frame)
                            $frameBitmap.Save($outPath, [System.Drawing.Imaging.ImageFormat]::Png)
                            $previewGraphics.DrawImageUnscaled($frameBitmap, $frame * 256, 0)
                            $bounds = Get-AlphaBounds $frameBitmap 16
                            Write-Output ('f{0}: bbox={1},{2},{3},{4} bottom={5}' -f $frame, $bounds.X, $bounds.Y, $bounds.Width, $bounds.Height, ($bounds.Bottom - 1))
                        }
                        finally { if ($null -ne $frameBitmap) { $frameBitmap.Dispose() } }
                    }
                    finally { $hires.Dispose() }
                }
            }
            finally { $previewGraphics.Dispose() }
            $preview.Save((Join-Path $PSScriptRoot 'preview_pace_SE.png'), [System.Drawing.Imaging.ImageFormat]::Png)
        }
        finally { $preview.Dispose() }
    }
    finally {
        $farHind.Dispose(); $nearHind.Dispose(); $farFore.Dispose(); $nearFore.Dispose(); $body.Dispose()
    }
}
finally { $source.Dispose() }
