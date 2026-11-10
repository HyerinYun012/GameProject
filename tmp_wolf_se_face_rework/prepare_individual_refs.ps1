$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

function Export-Cells {
    param(
        [Parameter(Mandatory = $true)][string]$SourcePath,
        [Parameter(Mandatory = $true)][string]$Prefix,
        [int]$CellWidth = 256,
        [int]$CellHeight = 256,
        [int]$Count = 6
    )

    $source = [System.Drawing.Bitmap]::new((Resolve-Path $SourcePath).Path)
    try {
        if ($source.Width -ne ($CellWidth * $Count) -or $source.Height -ne $CellHeight) {
            throw "Unexpected source size: $($source.Width)x$($source.Height)"
        }

        for ($frame = 0; $frame -lt $Count; $frame++) {
            $rect = [System.Drawing.Rectangle]::new($frame * $CellWidth, 0, $CellWidth, $CellHeight)
            $cell = $source.Clone($rect, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
            try {
                $cell.Save(
                    (Join-Path $PSScriptRoot ('{0}_{1}.png' -f $Prefix, $frame)),
                    [System.Drawing.Imaging.ImageFormat]::Png
                )
            }
            finally {
                $cell.Dispose()
            }
        }
    }
    finally {
        $source.Dispose()
    }
}

Export-Cells -SourcePath (Join-Path $PSScriptRoot 'ref_bear_SE_motion.png') -Prefix 'ref_bear_pose'
Export-Cells -SourcePath (Join-Path $PSScriptRoot 'ref_motion_guide.png') -Prefix 'ref_gait_pose'

$contactGuide = [System.Drawing.Bitmap]::new(512, 256, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
try {
    $graphics = [System.Drawing.Graphics]::FromImage($contactGuide)
    try {
        $graphics.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceCopy
        $graphics.Clear([System.Drawing.Color]::Transparent)

        foreach ($item in @(
            @{ Frame = 0; X = 0 },
            @{ Frame = 3; X = 256 }
        )) {
            $cell = [System.Drawing.Bitmap]::new((Join-Path $PSScriptRoot ('ref_gait_pose_{0}.png' -f $item.Frame)))
            try {
                $graphics.DrawImageUnscaled($cell, $item.X, 0)
            }
            finally {
                $cell.Dispose()
            }
        }
    }
    finally {
        $graphics.Dispose()
    }

    $contactGuide.Save(
        (Join-Path $PSScriptRoot 'ref_contact_extremes.png'),
        [System.Drawing.Imaging.ImageFormat]::Png
    )
}
finally {
    $contactGuide.Dispose()
}

Get-ChildItem -LiteralPath $PSScriptRoot -Filter 'ref_*_pose_*.png' |
    Sort-Object Name |
    Select-Object Name, Length
