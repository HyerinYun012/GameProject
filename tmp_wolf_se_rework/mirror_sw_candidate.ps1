$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$sheetPath = (Resolve-Path (Join-Path $PSScriptRoot '..\Assets\Sprites\Animals\Wolf\wolf_walk.png')).Path
$sheet = [System.Drawing.Bitmap]::new($sheetPath)
try {
    if ($sheet.Width -ne 1536 -or $sheet.Height -ne 2048) { throw "Unexpected wolf_walk size: $($sheet.Width)x$($sheet.Height)" }
    $preview = [System.Drawing.Bitmap]::new(1536, 256, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    try {
        $previewGraphics = [System.Drawing.Graphics]::FromImage($preview)
        try {
            $previewGraphics.Clear([System.Drawing.Color]::Transparent)
            $previewGraphics.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceCopy
            for ($frame = 0; $frame -lt 6; $frame++) {
                $cell = $sheet.Clone([System.Drawing.Rectangle]::new($frame * 256, 7 * 256, 256, 256), [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
                try {
                    $cell.RotateFlip([System.Drawing.RotateFlipType]::RotateNoneFlipX)
                    $path = Join-Path $PSScriptRoot ('mirror_SW_to_SE_{0}.png' -f $frame)
                    $cell.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
                    $previewGraphics.DrawImageUnscaled($cell, $frame * 256, 0)
                }
                finally { $cell.Dispose() }
            }
        }
        finally { $previewGraphics.Dispose() }
        $preview.Save((Join-Path $PSScriptRoot 'preview_mirror_SW_to_SE.png'), [System.Drawing.Imaging.ImageFormat]::Png)
    }
    finally { $preview.Dispose() }
}
finally { $sheet.Dispose() }

Get-ChildItem -LiteralPath $PSScriptRoot -Filter 'mirror_SW_to_SE_*.png' | Sort-Object Name | Select-Object Name, Length
