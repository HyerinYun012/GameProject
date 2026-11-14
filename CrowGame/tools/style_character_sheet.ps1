$ErrorActionPreference = 'Stop'

Add-Type -AssemblyName System.Drawing

$projectDir = Split-Path -Parent $PSScriptRoot
$characterDir = Join-Path $projectDir 'assets\Character Creation 32P\Character Creation 32P'
$sourcePath = Join-Path $characterDir 'Animations.png'
$outputPath = Join-Path $characterDir 'Animations Adventurer.png'

if (-not (Test-Path -LiteralPath $sourcePath)) {
    throw "Missing source sheet: $sourcePath"
}

# These are the three body-fill shades used by the original sprite.  The dark
# outline is deliberately left untouched so the original face, proportions,
# poses, tools, and one-pixel silhouette all remain exactly aligned.
$skinLight = '238,195,154'
$skinMid = '215,171,128'
$skinDark = '202,150,100'

$palettes = @{
    tunic = @{
        $skinLight = [System.Drawing.Color]::FromArgb(255, 126, 133, 75)
        $skinMid   = [System.Drawing.Color]::FromArgb(255, 100, 108, 59)
        $skinDark  = [System.Drawing.Color]::FromArgb(255, 73, 80, 42)
    }
    leather = @{
        $skinLight = [System.Drawing.Color]::FromArgb(255, 116, 70, 40)
        $skinMid   = [System.Drawing.Color]::FromArgb(255, 88, 48, 28)
        $skinDark  = [System.Drawing.Color]::FromArgb(255, 63, 34, 23)
    }
    trousers = @{
        $skinLight = [System.Drawing.Color]::FromArgb(255, 78, 72, 63)
        $skinMid   = [System.Drawing.Color]::FromArgb(255, 57, 52, 47)
        $skinDark  = [System.Drawing.Color]::FromArgb(255, 40, 37, 35)
    }
    boots = @{
        $skinLight = [System.Drawing.Color]::FromArgb(255, 101, 61, 37)
        $skinMid   = [System.Drawing.Color]::FromArgb(255, 75, 43, 28)
        $skinDark  = [System.Drawing.Color]::FromArgb(255, 50, 29, 22)
    }
}

$source = [System.Drawing.Bitmap]::new($sourcePath)
try {
    $output = [System.Drawing.Bitmap]::new(
        $source.Width,
        $source.Height,
        [System.Drawing.Imaging.PixelFormat]::Format32bppArgb
    )
    try {
        $graphics = [System.Drawing.Graphics]::FromImage($output)
        try {
            $graphics.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceCopy
            $graphics.DrawImageUnscaled($source, 0, 0)
        }
        finally {
            $graphics.Dispose()
        }

        for ($y = 0; $y -lt $output.Height; $y++) {
            $localY = $y % 48
            if ($localY -lt 29) {
                continue
            }

            for ($x = 0; $x -lt $output.Width; $x++) {
                $pixel = $output.GetPixel($x, $y)
                if ($pixel.A -eq 0) {
                    continue
                }
                $key = "$($pixel.R),$($pixel.G),$($pixel.B)"
                if ($key -notin @($skinLight, $skinMid, $skinDark)) {
                    continue
                }

                $localX = $x % 32
                if ($localY -eq 29 -and $localX -ge 13 -and $localX -le 18) {
                    # Keep only the narrow neck visible; cover the shoulders.
                    continue
                }
                if ($localY -le 37) {
                    $part = 'tunic'
                }
                elseif ($localY -le 40 -and ($localX -le 8 -or $localX -ge 23)) {
                    # Brown leather gloves make extended action hands readable.
                    $part = 'leather'
                }
                elseif ($localY -le 39) {
                    $part = 'leather'
                }
                elseif ($localY -le 43) {
                    $part = 'trousers'
                }
                else {
                    $part = 'boots'
                }
                $output.SetPixel($x, $y, $palettes[$part][$key])
            }
        }

        $output.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png)
    }
    finally {
        $output.Dispose()
    }
}
finally {
    $source.Dispose()
}

Write-Output "Styled $outputPath"
