$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$generatedRoot = 'C:\Users\hrin2\.codex\generated_images\01a1a5a8-6811-7c93-a543-536793c4de93'
$outputRoot = $PSScriptRoot
$targetColor = [System.Drawing.Color]::FromArgb(97, 88, 82)

$jobs = @(
    [pscustomobject]@{ Dir='SE'; Frame=0; Path=(Join-Path $outputRoot 'regen_SE_0.png'); X=64; Y=78; W=128; H=160 },
    [pscustomobject]@{ Dir='SE'; Frame=1; Path=(Join-Path $outputRoot 'regen_SE_1.png'); X=64; Y=78; W=128; H=160 },
    [pscustomobject]@{ Dir='SE'; Frame=2; Path=(Join-Path $outputRoot 'regen_SE_2.png'); X=64; Y=78; W=128; H=160 },
    [pscustomobject]@{ Dir='SE'; Frame=3; Path=(Join-Path $outputRoot 'regen_SE_3.png'); X=64; Y=78; W=128; H=160 },
    [pscustomobject]@{ Dir='SE'; Frame=4; Path=(Join-Path $outputRoot 'regen_SE_4.png'); X=64; Y=78; W=128; H=160 },
    [pscustomobject]@{ Dir='SE'; Frame=5; Path=(Join-Path $outputRoot 'regen_SE_5.png'); X=64; Y=78; W=128; H=160 },

    [pscustomobject]@{ Dir='E'; Frame=0; File='exec-9c9a6abc-1b3f-4700-b570-2661f7ea8714.png'; X=39; Y=91; W=178; H=147 },
    [pscustomobject]@{ Dir='E'; Frame=1; File='exec-b5e550f5-e1c6-47d8-91c7-5e03f3c50bbe.png'; X=39; Y=91; W=178; H=147 },
    [pscustomobject]@{ Dir='E'; Frame=2; File='exec-931d7732-ed6e-482a-bc5a-b5281dbe21ad.png'; X=39; Y=91; W=178; H=147 },
    [pscustomobject]@{ Dir='E'; Frame=3; File='exec-db208507-0a1c-4b18-8398-a4803b5323d0.png'; X=39; Y=91; W=178; H=147 },
    [pscustomobject]@{ Dir='E'; Frame=4; File='exec-4c4ef2e6-ab57-49e7-b606-6506c14ff2e5.png'; X=39; Y=91; W=178; H=147 },
    [pscustomobject]@{ Dir='E'; Frame=5; File='exec-deea6e38-ab56-4517-bdda-4940781e5647.png'; X=39; Y=91; W=178; H=147 },

    [pscustomobject]@{ Dir='NE'; Frame=0; Path=(Join-Path $outputRoot 'imagegen_NE_0.png'); X=36; Y=79; W=183; H=159 },
    [pscustomobject]@{ Dir='NE'; Frame=1; Path=(Join-Path $outputRoot 'imagegen_NE_1.png'); X=36; Y=79; W=183; H=159 },
    [pscustomobject]@{ Dir='NE'; Frame=2; Path=(Join-Path $outputRoot 'imagegen_NE_2.png'); X=36; Y=79; W=183; H=159 },
    [pscustomobject]@{ Dir='NE'; Frame=3; Path=(Join-Path $outputRoot 'imagegen_NE_3.png'); X=36; Y=79; W=183; H=159 },
    [pscustomobject]@{ Dir='NE'; Frame=4; Path=(Join-Path $outputRoot 'imagegen_NE_4.png'); X=36; Y=79; W=183; H=159 },
    [pscustomobject]@{ Dir='NE'; Frame=5; Path=(Join-Path $outputRoot 'imagegen_NE_5.png'); X=36; Y=79; W=183; H=159 },

    [pscustomobject]@{ Dir='N'; Frame=0; Path='C:\Users\hrin2\.codex\generated_images\01a1ab30-bae9-7290-ae89-215679c21292\exec-3ab8a14b-41dd-43a1-8488-09fb1956abf8.png'; X=70; Y=67; W=116; H=171 },
    [pscustomobject]@{ Dir='N'; Frame=1; Path='C:\Users\hrin2\.codex\generated_images\01a1ab30-bae9-7290-ae89-215679c21292\exec-a06d1f70-6b88-4aa4-9105-a4fc9ba14cf8.png'; X=70; Y=67; W=116; H=171 },
    [pscustomobject]@{ Dir='N'; Frame=2; Path='C:\Users\hrin2\.codex\generated_images\01a1ab30-bae9-7290-ae89-215679c21292\exec-9761c489-58ef-455c-9fcc-a940b8e6331f.png'; X=70; Y=67; W=116; H=171 },
    [pscustomobject]@{ Dir='N'; Frame=3; Path='C:\Users\hrin2\.codex\generated_images\01a1ab30-bae9-7290-ae89-215679c21292\exec-3f8ca55b-6fc3-4fc5-b732-2f87fefc7d08.png'; X=70; Y=67; W=116; H=171 },
    [pscustomobject]@{ Dir='N'; Frame=4; Path='C:\Users\hrin2\.codex\generated_images\01a1ab30-bae9-7290-ae89-215679c21292\exec-c67457f5-8451-4b2c-8845-6fd8c798825b.png'; X=70; Y=67; W=116; H=171 },
    [pscustomobject]@{ Dir='N'; Frame=5; Path='C:\Users\hrin2\.codex\generated_images\01a1ab30-bae9-7290-ae89-215679c21292\exec-2112eab1-68dd-437c-9c47-b709e05beb33.png'; X=70; Y=67; W=116; H=171 }
)

function Get-AlphaBounds {
    param([System.Drawing.Bitmap]$Bitmap, [int]$Threshold = 16)
    $minX = $Bitmap.Width
    $minY = $Bitmap.Height
    $maxX = -1
    $maxY = -1
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
    if ($maxX -lt 0) { throw 'No opaque pixels found.' }
    return [System.Drawing.Rectangle]::new($minX, $minY, $maxX - $minX + 1, $maxY - $minY + 1)
}

function Normalize-Color {
    param([System.Drawing.Bitmap]$Bitmap)
    [long]$sumR = 0
    [long]$sumG = 0
    [long]$sumB = 0
    [long]$count = 0
    for ($y = 0; $y -lt $Bitmap.Height; $y++) {
        for ($x = 0; $x -lt $Bitmap.Width; $x++) {
            $c = $Bitmap.GetPixel($x, $y)
            if ($c.A -ge 64) {
                $sumR += $c.R
                $sumG += $c.G
                $sumB += $c.B
                $count++
            }
        }
    }
    if ($count -eq 0) { return }
    $dr = $targetColor.R - [int]($sumR / $count)
    $dg = $targetColor.G - [int]($sumG / $count)
    $db = $targetColor.B - [int]($sumB / $count)
    for ($y = 0; $y -lt $Bitmap.Height; $y++) {
        for ($x = 0; $x -lt $Bitmap.Width; $x++) {
            $c = $Bitmap.GetPixel($x, $y)
            if ($c.A -lt 16) {
                $Bitmap.SetPixel($x, $y, [System.Drawing.Color]::Transparent)
                continue
            }
            $r = [Math]::Max(0, [Math]::Min(255, $c.R + $dr))
            $g = [Math]::Max(0, [Math]::Min(255, $c.G + $dg))
            $b = [Math]::Max(0, [Math]::Min(255, $c.B + $db))
            $Bitmap.SetPixel($x, $y, [System.Drawing.Color]::FromArgb($c.A, $r, $g, $b))
        }
    }
}

foreach ($job in $jobs) {
    $sourcePath = if ($job.PSObject.Properties.Name -contains 'Path') { $job.Path } else { Join-Path $generatedRoot $job.File }
    $source = [System.Drawing.Bitmap]::new($sourcePath)
    try {
        $bounds = Get-AlphaBounds -Bitmap $source
        $output = [System.Drawing.Bitmap]::new(256, 256, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
        try {
            $g = [System.Drawing.Graphics]::FromImage($output)
            try {
                $g.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceCopy
                $g.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
                $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
                $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
                $g.Clear([System.Drawing.Color]::Transparent)
                $destination = [System.Drawing.Rectangle]::new($job.X, $job.Y, $job.W, $job.H)
                $g.DrawImage($source, $destination, $bounds, [System.Drawing.GraphicsUnit]::Pixel)
            }
            finally {
                $g.Dispose()
            }
            Normalize-Color -Bitmap $output
            $output.Save((Join-Path $outputRoot ('styled_{0}_{1}.png' -f $job.Dir, $job.Frame)), [System.Drawing.Imaging.ImageFormat]::Png)
        }
        finally {
            $output.Dispose()
        }
    }
    finally {
        $source.Dispose()
    }
}

function Split-NorthCentralLeg {
    param([string]$Path)
    $tempPath = $Path + '.split.png'
    if (Test-Path -LiteralPath $tempPath) { Remove-Item -LiteralPath $tempPath -Force }
    $loaded = [System.Drawing.Bitmap]::new($Path)
    try {
        $source = $loaded.Clone([System.Drawing.Rectangle]::new(0, 0, $loaded.Width, $loaded.Height), [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    }
    finally { $loaded.Dispose() }
    try {
        $leg = $source.Clone([System.Drawing.Rectangle]::new(121, 180, 18, 38), [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
        try {
            $output = [System.Drawing.Bitmap]::new($source.Width, $source.Height, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
            try {
                $g = [System.Drawing.Graphics]::FromImage($output)
                try {
                    $g.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceCopy
                    $g.DrawImageUnscaled($source, 0, 0)
                    $clear = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::Transparent)
                    try { $g.FillRectangle($clear, 120, 180, 24, 38) }
                    finally { $clear.Dispose() }
                    $g.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceOver
                    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
                    $g.DrawImage($leg, [System.Drawing.Rectangle]::new(121, 180, 14, 38))
                    $g.DrawImage($leg, [System.Drawing.Rectangle]::new(138, 180, 14, 38))
                }
                finally { $g.Dispose() }
                $output.Save($tempPath, [System.Drawing.Imaging.ImageFormat]::Png)
            }
            finally { $output.Dispose() }
        }
        finally { $leg.Dispose() }
    }
    finally { $source.Dispose() }
    Move-Item -LiteralPath $tempPath -Destination $Path -Force
}

for ($frame = 0; $frame -lt 6; $frame++) {
    Split-NorthCentralLeg -Path (Join-Path $outputRoot ('styled_N_{0}.png' -f $frame))
}

function Apply-LegCue {
    param(
        [string]$Path,
        [object[]]$Operations
    )
    $tempPath = $Path + '.cue.png'
    if (Test-Path -LiteralPath $tempPath) { Remove-Item -LiteralPath $tempPath -Force }
    $loaded = [System.Drawing.Bitmap]::new($Path)
    try {
        $bitmap = $loaded.Clone([System.Drawing.Rectangle]::new(0, 0, $loaded.Width, $loaded.Height), [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    }
    finally { $loaded.Dispose() }
    try {
        foreach ($op in $Operations) {
            for ($y = $op.Y; $y -lt ($op.Y + $op.H); $y++) {
                for ($x = $op.X; $x -lt ($op.X + $op.W); $x++) {
                    $c = $bitmap.GetPixel($x, $y)
                    if ($c.A -lt 16) { continue }
                    if ($op.Clear) {
                        $bitmap.SetPixel($x, $y, [System.Drawing.Color]::Transparent)
                        continue
                    }
                    $edgeX = [Math]::Min($x - $op.X, ($op.X + $op.W - 1) - $x) / 4.0
                    $edgeY = ($y - $op.Y) / 9.0
                    $blend = [Math]::Max(0.0, [Math]::Min(1.0, [Math]::Min($edgeX, $edgeY)))
                    $factor = 1.0 + (($op.Factor - 1.0) * $blend)
                    $r = [Math]::Max(0, [Math]::Min(255, [int][Math]::Round($c.R * $factor)))
                    $g = [Math]::Max(0, [Math]::Min(255, [int][Math]::Round($c.G * $factor)))
                    $b = [Math]::Max(0, [Math]::Min(255, [int][Math]::Round($c.B * $factor)))
                    $bitmap.SetPixel($x, $y, [System.Drawing.Color]::FromArgb($c.A, $r, $g, $b))
                }
            }
        }
        $bitmap.Save($tempPath, [System.Drawing.Imaging.ImageFormat]::Png)
    }
    finally { $bitmap.Dispose() }
    Move-Item -LiteralPath $tempPath -Destination $Path -Force
}

# E: make the synchronized pair visually unambiguous.  The brighter, foreground
# fore/hind pair share the same forward/back phase; the opposite pair recedes.
Apply-LegCue -Path (Join-Path $outputRoot 'styled_E_0.png') -Operations @(
    [pscustomobject]@{ X=34;  Y=178; W=42; H=61; Factor=0.72; Clear=$false },
    [pscustomobject]@{ X=118; Y=178; W=49; H=61; Factor=0.72; Clear=$false },
    [pscustomobject]@{ X=78;  Y=178; W=44; H=61; Factor=1.16; Clear=$false },
    [pscustomobject]@{ X=172; Y=178; W=49; H=61; Factor=1.16; Clear=$false }
)
Apply-LegCue -Path (Join-Path $outputRoot 'styled_E_1.png') -Operations @(
    [pscustomobject]@{ X=43;  Y=178; W=31; H=61; Factor=0.72; Clear=$false },
    [pscustomobject]@{ X=108; Y=178; W=35; H=61; Factor=0.72; Clear=$false },
    [pscustomobject]@{ X=75;  Y=178; W=31; H=61; Factor=1.16; Clear=$false },
    [pscustomobject]@{ X=160; Y=178; W=35; H=61; Factor=1.16; Clear=$false }
)
Apply-LegCue -Path (Join-Path $outputRoot 'styled_E_2.png') -Operations @(
    [pscustomobject]@{ X=112; Y=195; W=24; H=33; Factor=1.0; Clear=$true },
    [pscustomobject]@{ X=80;  Y=178; W=31; H=61; Factor=0.72; Clear=$false },
    [pscustomobject]@{ X=181; Y=178; W=38; H=61; Factor=0.72; Clear=$false },
    [pscustomobject]@{ X=43;  Y=178; W=32; H=61; Factor=1.16; Clear=$false },
    [pscustomobject]@{ X=137; Y=178; W=32; H=61; Factor=1.16; Clear=$false }
)
Apply-LegCue -Path (Join-Path $outputRoot 'styled_E_3.png') -Operations @(
    [pscustomobject]@{ X=92;  Y=178; W=34; H=61; Factor=0.72; Clear=$false },
    [pscustomobject]@{ X=177; Y=178; W=39; H=61; Factor=0.72; Clear=$false },
    [pscustomobject]@{ X=32;  Y=178; W=36; H=61; Factor=1.16; Clear=$false },
    [pscustomobject]@{ X=130; Y=178; W=37; H=61; Factor=1.16; Clear=$false }
)

function Shift-ImageRegion {
    param(
        [string]$Path,
        [System.Drawing.Rectangle]$SourceRect,
        [System.Drawing.Point]$Destination
    )
    $tempPath = $Path + '.shift.png'
    if (Test-Path -LiteralPath $tempPath) { Remove-Item -LiteralPath $tempPath -Force }
    $loaded = [System.Drawing.Bitmap]::new($Path)
    try {
        $bitmap = $loaded.Clone([System.Drawing.Rectangle]::new(0, 0, $loaded.Width, $loaded.Height), [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    }
    finally { $loaded.Dispose() }
    try {
        $piece = $bitmap.Clone($SourceRect, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
        try {
            $g = [System.Drawing.Graphics]::FromImage($bitmap)
            try {
                $g.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceCopy
                $clear = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::Transparent)
                try { $g.FillRectangle($clear, $SourceRect) }
                finally { $clear.Dispose() }
                $g.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceOver
                $g.DrawImageUnscaled($piece, $Destination)
            }
            finally { $g.Dispose() }
        }
        finally { $piece.Dispose() }
        $bitmap.Save($tempPath, [System.Drawing.Imaging.ImageFormat]::Png)
    }
    finally { $bitmap.Dispose() }
    Move-Item -LiteralPath $tempPath -Destination $Path -Force
}

function Warp-EastFarHindLeg {
    param([string]$Path)
    $tempPath = $Path + '.warp.png'
    if (Test-Path -LiteralPath $tempPath) { Remove-Item -LiteralPath $tempPath -Force }
    $loaded = [System.Drawing.Bitmap]::new($Path)
    try {
        $source = $loaded.Clone([System.Drawing.Rectangle]::new(0, 0, $loaded.Width, $loaded.Height), [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
        $output = $loaded.Clone([System.Drawing.Rectangle]::new(0, 0, $loaded.Width, $loaded.Height), [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    }
    finally { $loaded.Dispose() }
    try {
        for ($y = 190; $y -le 235; $y++) {
            $offset = -[int][Math]::Round(8.0 * [Math]::Min(1.0, ($y - 190) / 12.0))
            for ($x = 42; $x -le 69; $x++) {
                $c = $source.GetPixel($x, $y)
                if ($c.A -ge 16) { $output.SetPixel($x, $y, [System.Drawing.Color]::Transparent) }
            }
            for ($x = 42; $x -le 69; $x++) {
                $c = $source.GetPixel($x, $y)
                if ($c.A -ge 16) { $output.SetPixel($x + $offset, $y, $c) }
            }
        }
        $output.Save($tempPath, [System.Drawing.Imaging.ImageFormat]::Png)
    }
    finally {
        $source.Dispose()
        $output.Dispose()
    }
    Move-Item -LiteralPath $tempPath -Destination $Path -Force
}

# Frame 1: bend only the distant hind lower leg rearward.  Offset starts at
# zero at the hip and reaches eight pixels at the paw, avoiding a cut seam.
Warp-EastFarHindLeg -Path (Join-Path $outputRoot 'styled_E_1.png')

# NE f0-f2 use the rearward foreground pair; f3 switches foreground depth to
# the opposite forward pair, creating the missing contact extreme.
foreach ($frame in 0, 1, 2) {
    Apply-LegCue -Path (Join-Path $outputRoot ('styled_NE_{0}.png' -f $frame)) -Operations @(
        [pscustomobject]@{ X=94;  Y=174; W=29; H=65; Factor=0.72; Clear=$false },
        [pscustomobject]@{ X=162; Y=174; W=38; H=65; Factor=0.72; Clear=$false },
        [pscustomobject]@{ X=52;  Y=174; W=43; H=65; Factor=1.16; Clear=$false },
        [pscustomobject]@{ X=122; Y=174; W=38; H=65; Factor=1.16; Clear=$false }
    )
}
Apply-LegCue -Path (Join-Path $outputRoot 'styled_NE_3.png') -Operations @(
    [pscustomobject]@{ X=52;  Y=174; W=43; H=65; Factor=0.72; Clear=$false },
    [pscustomobject]@{ X=122; Y=174; W=38; H=65; Factor=0.72; Clear=$false },
    [pscustomobject]@{ X=94;  Y=174; W=29; H=65; Factor=1.16; Clear=$false },
    [pscustomobject]@{ X=162; Y=174; W=38; H=65; Factor=1.16; Clear=$false }
)

# Use a symmetric six-frame phase order so each same-side pair reverses together
# and the loop returns through the same intermediate silhouettes.
Copy-Item -LiteralPath (Join-Path $outputRoot 'styled_SE_2.png') -Destination (Join-Path $outputRoot 'styled_SE_4.png') -Force
Copy-Item -LiteralPath (Join-Path $outputRoot 'styled_SE_1.png') -Destination (Join-Path $outputRoot 'styled_SE_5.png') -Force
Copy-Item -LiteralPath (Join-Path $outputRoot 'styled_E_2.png') -Destination (Join-Path $outputRoot 'styled_E_4.png') -Force
Copy-Item -LiteralPath (Join-Path $outputRoot 'styled_E_1.png') -Destination (Join-Path $outputRoot 'styled_E_5.png') -Force
Copy-Item -LiteralPath (Join-Path $outputRoot 'styled_NE_2.png') -Destination (Join-Path $outputRoot 'styled_NE_4.png') -Force
Copy-Item -LiteralPath (Join-Path $outputRoot 'styled_NE_1.png') -Destination (Join-Path $outputRoot 'styled_NE_5.png') -Force
Copy-Item -LiteralPath (Join-Path $outputRoot 'styled_N_2.png') -Destination (Join-Path $outputRoot 'styled_N_4.png') -Force
Copy-Item -LiteralPath (Join-Path $outputRoot 'styled_N_1.png') -Destination (Join-Path $outputRoot 'styled_N_5.png') -Force

for ($frame = 0; $frame -lt 6; $frame++) {
    $ne = [System.Drawing.Bitmap]::new((Join-Path $outputRoot ('styled_NE_{0}.png' -f $frame)))
    try {
        $ne.RotateFlip([System.Drawing.RotateFlipType]::RotateNoneFlipX)
        $ne.Save((Join-Path $outputRoot ('styled_NW_{0}.png' -f $frame)), [System.Drawing.Imaging.ImageFormat]::Png)
    }
    finally { $ne.Dispose() }
}

Get-ChildItem -LiteralPath $outputRoot -Filter 'styled_*.png' | Sort-Object Name | Select-Object Name, Length
