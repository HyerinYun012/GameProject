$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$guide = [System.Drawing.Bitmap]::new((Resolve-Path (Join-Path $PSScriptRoot 'ref_e_pace_guide.png')).Path)
try {
    if ($guide.Width -ne 1536 -or $guide.Height -ne 256) { throw 'Unexpected pace guide size.' }
    for ($frame = 0; $frame -lt 6; $frame++) {
        $cell = $guide.Clone(
            [System.Drawing.Rectangle]::new($frame * 256, 0, 256, 256),
            [System.Drawing.Imaging.PixelFormat]::Format32bppArgb
        )
        try {
            $cell.Save((Join-Path $PSScriptRoot ('ref_e_pace_f{0}.png' -f $frame)), [System.Drawing.Imaging.ImageFormat]::Png)
        }
        finally { $cell.Dispose() }
    }
}
finally { $guide.Dispose() }
