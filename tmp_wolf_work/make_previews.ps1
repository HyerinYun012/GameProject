$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$root = $PSScriptRoot
$dirs = @('SE', 'E', 'NE', 'N', 'NW')

foreach ($dir in $dirs) {
    $sheet = [System.Drawing.Bitmap]::new(1536, 256, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    try {
        $g = [System.Drawing.Graphics]::FromImage($sheet)
        try {
            $g.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceCopy
            $g.Clear([System.Drawing.Color]::Transparent)
            for ($frame = 0; $frame -lt 6; $frame++) {
                $src = [System.Drawing.Bitmap]::new((Join-Path $root ('final_{0}_{1}.png' -f $dir, $frame)))
                try {
                    $g.DrawImageUnscaled($src, $frame * 256, 0)
                }
                finally {
                    $src.Dispose()
                }
            }
        }
        finally {
            $g.Dispose()
        }
        $sheet.Save((Join-Path $root ('preview_{0}.png' -f $dir)), [System.Drawing.Imaging.ImageFormat]::Png)
    }
    finally {
        $sheet.Dispose()
    }
}

$sourcePath = Join-Path (Split-Path -Parent $root) 'Assets/Sprites/Animals/Wolf/wolf_walk.png'
$candidatePath = Join-Path $root 'wolf_walk_candidate.png'
$candidate = [System.Drawing.Bitmap]::new($sourcePath)
try {
        $g = [System.Drawing.Graphics]::FromImage($candidate)
        try {
            $g.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceCopy
            $rowByDir = @{ SE = 1; E = 2; NE = 3; N = 4; NW = 5 }
            foreach ($dir in $dirs) {
                $clear = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::Transparent)
                try {
                    $g.FillRectangle($clear, 0, $rowByDir[$dir] * 256, 1536, 256)
                }
                finally {
                    $clear.Dispose()
                }
                for ($frame = 0; $frame -lt 6; $frame++) {
                    $src = [System.Drawing.Bitmap]::new((Join-Path $root ('final_{0}_{1}.png' -f $dir, $frame)))
                    try {
                        $g.DrawImageUnscaled($src, $frame * 256, $rowByDir[$dir] * 256)
                    }
                    finally {
                        $src.Dispose()
                    }
                }
            }
        }
        finally {
            $g.Dispose()
        }
        $candidate.Save($candidatePath, [System.Drawing.Imaging.ImageFormat]::Png)
}
finally { $candidate.Dispose() }

Get-ChildItem -LiteralPath $root -Filter 'preview_*.png' | Sort-Object Name | Select-Object Name, Length
Get-Item -LiteralPath $candidatePath | Select-Object Name, Length

$styledDirs = @('SE', 'E', 'NE', 'N', 'NW')
foreach ($dir in $styledDirs) {
    $first = Join-Path $root ('styled_{0}_0.png' -f $dir)
    if (-not (Test-Path -LiteralPath $first)) { continue }
    $sheet = [System.Drawing.Bitmap]::new(1536, 256, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    try {
        $g = [System.Drawing.Graphics]::FromImage($sheet)
        try {
            $g.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceCopy
            $g.Clear([System.Drawing.Color]::Transparent)
            for ($frame = 0; $frame -lt 6; $frame++) {
                $src = [System.Drawing.Bitmap]::new((Join-Path $root ('styled_{0}_{1}.png' -f $dir, $frame)))
                try { $g.DrawImageUnscaled($src, $frame * 256, 0) }
                finally { $src.Dispose() }
            }
        }
        finally { $g.Dispose() }
        $sheet.Save((Join-Path $root ('preview_styled_{0}.png' -f $dir)), [System.Drawing.Imaging.ImageFormat]::Png)
    }
    finally { $sheet.Dispose() }
}

$styledCandidatePath = Join-Path $root 'wolf_walk_styled_candidate.png'
$candidate = [System.Drawing.Bitmap]::new($sourcePath)
try {
        $g = [System.Drawing.Graphics]::FromImage($candidate)
        try {
            $g.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceCopy
            $rowByDir = @{ SE = 1; E = 2; NE = 3; N = 4; NW = 5 }
            foreach ($dir in $styledDirs) {
                $clear = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::Transparent)
                try { $g.FillRectangle($clear, 0, $rowByDir[$dir] * 256, 1536, 256) }
                finally { $clear.Dispose() }
                for ($frame = 0; $frame -lt 6; $frame++) {
                    $src = [System.Drawing.Bitmap]::new((Join-Path $root ('styled_{0}_{1}.png' -f $dir, $frame)))
                    try { $g.DrawImageUnscaled($src, $frame * 256, $rowByDir[$dir] * 256) }
                    finally { $src.Dispose() }
                }
            }
        }
        finally { $g.Dispose() }
        $candidate.Save($styledCandidatePath, [System.Drawing.Imaging.ImageFormat]::Png)
}
finally { $candidate.Dispose() }
