$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$sourcePath = Join-Path $PSScriptRoot '..\tmp_wolf_work\styled_SE_0.png'
$outputPath = Join-Path $PSScriptRoot 'inspect_styled_SE_0_grid.png'
$source = [System.Drawing.Bitmap]::new((Resolve-Path $sourcePath).Path)
try {
    $scale = 4
    $output = [System.Drawing.Bitmap]::new(1024, 1024, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    try {
        $g = [System.Drawing.Graphics]::FromImage($output)
        try {
            $g.Clear([System.Drawing.Color]::FromArgb(255, 38, 42, 44))
            $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::NearestNeighbor
            $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::Half
            $g.DrawImage($source, [System.Drawing.Rectangle]::new(0, 0, 1024, 1024), [System.Drawing.Rectangle]::new(0, 0, 256, 256), [System.Drawing.GraphicsUnit]::Pixel)

            $gridPen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(90, 80, 220, 255), 1)
            $majorPen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(180, 255, 190, 60), 2)
            $font = [System.Drawing.Font]::new('Arial', 13, [System.Drawing.FontStyle]::Bold)
            $brush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::White)
            try {
                for ($i = 0; $i -le 256; $i += 8) {
                    $p = if (($i % 32) -eq 0) { $majorPen } else { $gridPen }
                    $coord = $i * $scale
                    $g.DrawLine($p, $coord, 0, $coord, 1024)
                    $g.DrawLine($p, 0, $coord, 1024, $coord)
                    if (($i % 32) -eq 0 -and $i -lt 256) {
                        $g.DrawString([string]$i, $font, $brush, $coord + 3, 3)
                        $g.DrawString([string]$i, $font, $brush, 3, $coord + 3)
                    }
                }
            }
            finally {
                $gridPen.Dispose(); $majorPen.Dispose(); $font.Dispose(); $brush.Dispose()
            }
        }
        finally { $g.Dispose() }
        $output.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png)
    }
    finally { $output.Dispose() }
}
finally { $source.Dispose() }

Get-Item -LiteralPath $outputPath | Select-Object FullName, Length
