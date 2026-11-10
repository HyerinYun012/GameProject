$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

function Export-Strip {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][int]$Columns,
        [Parameter(Mandatory = $true)][int]$Row,
        [Parameter(Mandatory = $true)][string]$Output
    )

    $bitmap = [System.Drawing.Bitmap]::new($Source)
    try {
        $expectedWidth = $Columns * 256
        if ($bitmap.Width -ne $expectedWidth -or $bitmap.Height -ne 2048) {
            throw "Unexpected sheet size for $Source`: $($bitmap.Width)x$($bitmap.Height)"
        }

        $rect = [System.Drawing.Rectangle]::new(0, $Row * 256, $expectedWidth, 256)
        $strip = $bitmap.Clone($rect, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
        try {
            $strip.Save($Output, [System.Drawing.Imaging.ImageFormat]::Png)
        }
        finally {
            $strip.Dispose()
        }
    }
    finally {
        $bitmap.Dispose()
    }
}

Export-Strip `
    -Source (Join-Path $root 'Assets\Sprites\Animals\Bear\bear_walk.png') `
    -Columns 6 -Row 1 `
    -Output (Join-Path $PSScriptRoot 'ref_bear_SE_motion.png')

Export-Strip `
    -Source (Join-Path $root 'Assets\Sprites\Animals\Wolf\wolf_idle.png') `
    -Columns 4 -Row 1 `
    -Output (Join-Path $PSScriptRoot 'ref_wolf_SE_idle_identity.png')

Export-Strip `
    -Source (Join-Path $root 'Assets\Sprites\Animals\Wolf\wolf_attack.png') `
    -Columns 6 -Row 1 `
    -Output (Join-Path $PSScriptRoot 'ref_wolf_SE_attack_style.png')

Export-Strip `
    -Source (Join-Path $root 'Assets\Sprites\Animals\Wolf\wolf_walk.png') `
    -Columns 6 -Row 1 `
    -Output (Join-Path $PSScriptRoot 'old_wolf_SE_rejected.png')

Get-ChildItem -LiteralPath $PSScriptRoot -Filter '*.png' |
    Sort-Object Name |
    Select-Object Name, Length
