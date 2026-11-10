$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$wolfDir = Join-Path $root 'Assets\Sprites\Animals\Wolf'
$bearDir = Join-Path $root 'Assets\Sprites\Animals\Bear'
$row = 3

function Export-Row {
    param([string]$SourcePath, [int]$FrameCount, [string]$OutputName)
    $source = [System.Drawing.Bitmap]::new($SourcePath)
    try {
        $expectedWidth = $FrameCount * 256
        if ($source.Width -ne $expectedWidth -or $source.Height -ne 2048) {
            throw "Unexpected sheet dimensions for ${SourcePath}: $($source.Width)x$($source.Height)"
        }
        $rect = [System.Drawing.Rectangle]::new(0, $row * 256, $expectedWidth, 256)
        $strip = $source.Clone($rect, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
        try { $strip.Save((Join-Path $PSScriptRoot $OutputName), [System.Drawing.Imaging.ImageFormat]::Png) }
        finally { $strip.Dispose() }
    }
    finally { $source.Dispose() }
}

Export-Row (Join-Path $wolfDir 'wolf_walk.png') 6 'ref_wolf_walk_NE_current.png'
Export-Row (Join-Path $wolfDir 'wolf_idle.png') 4 'ref_wolf_idle_NE.png'
Export-Row (Join-Path $wolfDir 'wolf_attack.png') 6 'ref_wolf_attack_NE.png'
Export-Row (Join-Path $wolfDir 'wolf_hurt.png') 3 'ref_wolf_hurt_NE.png'
Export-Row (Join-Path $wolfDir 'wolf_death.png') 6 'ref_wolf_death_NE.png'
Export-Row (Join-Path $bearDir 'bear_walk.png') 6 'ref_bear_walk_NE.png'

$bearStripPath = Resolve-Path (Join-Path $PSScriptRoot 'ref_bear_walk_NE.png')
$bearStrip = [System.Drawing.Bitmap]::new($bearStripPath.Path)
try {
    for ($frame = 0; $frame -lt 6; $frame++) {
        $cell = $bearStrip.Clone(
            [System.Drawing.Rectangle]::new($frame * 256, 0, 256, 256),
            [System.Drawing.Imaging.PixelFormat]::Format32bppArgb
        )
        try { $cell.Save((Join-Path $PSScriptRoot ('ref_bear_walk_NE_F{0}.png' -f $frame)), [System.Drawing.Imaging.ImageFormat]::Png) }
        finally { $cell.Dispose() }
    }
}
finally { $bearStrip.Dispose() }

foreach ($identityStripName in @('ref_wolf_idle_NE.png', 'ref_wolf_attack_NE.png', 'ref_wolf_death_NE.png')) {
    $identityStripPath = Resolve-Path (Join-Path $PSScriptRoot $identityStripName)
    $identityStrip = [System.Drawing.Bitmap]::new($identityStripPath.Path)
    try {
        $identityCell = $identityStrip.Clone(
            [System.Drawing.Rectangle]::new(0, 0, 256, 256),
            [System.Drawing.Imaging.PixelFormat]::Format32bppArgb
        )
        try {
            $identityOutputName = ([System.IO.Path]::GetFileNameWithoutExtension($identityStripName)) + '_F0.png'
            $identityCell.Save((Join-Path $PSScriptRoot $identityOutputName), [System.Drawing.Imaging.ImageFormat]::Png)
        }
        finally { $identityCell.Dispose() }
    }
    finally { $identityStrip.Dispose() }
}

Get-ChildItem -LiteralPath $PSScriptRoot -Filter 'ref_*_NE*.png' | Sort-Object Name | Select-Object Name,Length,LastWriteTime
