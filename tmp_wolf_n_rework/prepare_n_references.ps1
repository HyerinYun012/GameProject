$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$wolfDir = Join-Path $root 'Assets\Sprites\Animals\Wolf'
$bearDir = Join-Path $root 'Assets\Sprites\Animals\Bear'
$row = 4

function Export-Row {
    param([string]$SourcePath, [int]$FrameCount, [string]$OutputName)
    $source = [System.Drawing.Bitmap]::new($SourcePath)
    try {
        $expectedWidth = $FrameCount * 256
        if ($source.Width -ne $expectedWidth -or $source.Height -ne 2048) {
            throw "Unexpected sheet dimensions for ${SourcePath}: $($source.Width)x$($source.Height)"
        }
        $strip = $source.Clone(
            [System.Drawing.Rectangle]::new(0, $row * 256, $expectedWidth, 256),
            [System.Drawing.Imaging.PixelFormat]::Format32bppArgb
        )
        try { $strip.Save((Join-Path $PSScriptRoot $OutputName), [System.Drawing.Imaging.ImageFormat]::Png) }
        finally { $strip.Dispose() }
    }
    finally { $source.Dispose() }
}

Export-Row (Join-Path $wolfDir 'wolf_walk.png') 6 'ref_wolf_walk_N_current.png'
Export-Row (Join-Path $wolfDir 'wolf_idle.png') 4 'ref_wolf_idle_N.png'
Export-Row (Join-Path $wolfDir 'wolf_attack.png') 6 'ref_wolf_attack_N.png'
Export-Row (Join-Path $wolfDir 'wolf_hurt.png') 3 'ref_wolf_hurt_N.png'
Export-Row (Join-Path $wolfDir 'wolf_death.png') 6 'ref_wolf_death_N.png'
Export-Row (Join-Path $bearDir 'bear_walk.png') 6 'ref_bear_walk_N.png'

foreach ($stripName in @('ref_wolf_idle_N.png', 'ref_wolf_attack_N.png', 'ref_wolf_death_N.png')) {
    $stripPath = Resolve-Path (Join-Path $PSScriptRoot $stripName)
    $strip = [System.Drawing.Bitmap]::new($stripPath.Path)
    try {
        $cell = $strip.Clone([System.Drawing.Rectangle]::new(0, 0, 256, 256), [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
        try {
            $output = ([System.IO.Path]::GetFileNameWithoutExtension($stripName)) + '_F0.png'
            $cell.Save((Join-Path $PSScriptRoot $output), [System.Drawing.Imaging.ImageFormat]::Png)
        }
        finally { $cell.Dispose() }
    }
    finally { $strip.Dispose() }
}

$bearStrip = [System.Drawing.Bitmap]::new((Resolve-Path (Join-Path $PSScriptRoot 'ref_bear_walk_N.png')).Path)
try {
    for ($frame = 0; $frame -lt 6; $frame++) {
        $cell = $bearStrip.Clone([System.Drawing.Rectangle]::new($frame * 256, 0, 256, 256), [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
        try { $cell.Save((Join-Path $PSScriptRoot ('ref_bear_walk_N_F{0}.png' -f $frame)), [System.Drawing.Imaging.ImageFormat]::Png) }
        finally { $cell.Dispose() }
    }
}
finally { $bearStrip.Dispose() }

Get-ChildItem -LiteralPath $PSScriptRoot -Filter 'ref_*_N*.png' | Sort-Object Name | Select-Object Name,Length,LastWriteTime
