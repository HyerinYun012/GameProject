param(
    [string]$FrameDirectory = $PSScriptRoot,
    [string]$CandidatePath = (Join-Path $PSScriptRoot 'wolf_walk_ne_candidate.png')
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Security

$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$sourcePath = Join-Path $root 'Assets\Sprites\Animals\Wolf\wolf_walk.png'
$targetRow = 3

function Get-RectHash([System.Drawing.Bitmap]$Bitmap, [System.Drawing.Rectangle]$Rect) {
    $clone = $Bitmap.Clone($Rect, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    try {
        $data = $clone.LockBits([System.Drawing.Rectangle]::new(0, 0, $clone.Width, $clone.Height), [System.Drawing.Imaging.ImageLockMode]::ReadOnly, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
        try {
            $length = [Math]::Abs($data.Stride) * $clone.Height
            $bytes = [byte[]]::new($length)
            [System.Runtime.InteropServices.Marshal]::Copy($data.Scan0, $bytes, 0, $length)
        }
        finally { $clone.UnlockBits($data) }
        $sha = [System.Security.Cryptography.SHA256]::Create()
        try { return [Convert]::ToHexString($sha.ComputeHash($bytes)) }
        finally { $sha.Dispose() }
    }
    finally { $clone.Dispose() }
}

function Copy-BitmapCellExact([System.Drawing.Bitmap]$Source, [System.Drawing.Bitmap]$Destination, [int]$DestinationX, [int]$DestinationY) {
    $sourceData = $Source.LockBits([System.Drawing.Rectangle]::new(0, 0, 256, 256), [System.Drawing.Imaging.ImageLockMode]::ReadOnly, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    try {
        $destinationData = $Destination.LockBits([System.Drawing.Rectangle]::new($DestinationX, $DestinationY, 256, 256), [System.Drawing.Imaging.ImageLockMode]::WriteOnly, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
        try {
            $rowBytes = 256 * 4
            $buffer = [byte[]]::new($rowBytes)
            for ($y = 0; $y -lt 256; $y++) {
                [System.Runtime.InteropServices.Marshal]::Copy([IntPtr]::Add($sourceData.Scan0, $y * $sourceData.Stride), $buffer, 0, $rowBytes)
                [System.Runtime.InteropServices.Marshal]::Copy($buffer, 0, [IntPtr]::Add($destinationData.Scan0, $y * $destinationData.Stride), $rowBytes)
            }
        }
        finally { $Destination.UnlockBits($destinationData) }
    }
    finally { $Source.UnlockBits($sourceData) }
}

$loaded = [System.Drawing.Bitmap]::new($sourcePath)
try {
    if ($loaded.Width -ne 1536 -or $loaded.Height -ne 2048) { throw "Unexpected wolf_walk size: $($loaded.Width)x$($loaded.Height)" }
    $candidate = $loaded.Clone([System.Drawing.Rectangle]::new(0, 0, $loaded.Width, $loaded.Height), [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
}
finally { $loaded.Dispose() }

try {
    for ($frame = 0; $frame -lt 6; $frame++) {
        $sprite = [System.Drawing.Bitmap]::new((Join-Path $FrameDirectory ('sequence_NE_{0}.png' -f $frame)))
        try { Copy-BitmapCellExact $sprite $candidate ($frame * 256) ($targetRow * 256) }
        finally { $sprite.Dispose() }
    }
    $candidate.Save($CandidatePath, [System.Drawing.Imaging.ImageFormat]::Png)
}
finally { $candidate.Dispose() }

$before = [System.Drawing.Bitmap]::new($sourcePath)
$after = [System.Drawing.Bitmap]::new($CandidatePath)
try {
    for ($row = 0; $row -lt 8; $row++) {
        $rect = [System.Drawing.Rectangle]::new(0, $row * 256, 1536, 256)
        $beforeHash = Get-RectHash $before $rect
        $afterHash = Get-RectHash $after $rect
        if ($row -eq $targetRow) {
            if ($beforeHash -eq $afterHash) { throw 'NE row did not change.' }
            Write-Output "row$row NE changed (expected)"
        }
        else {
            if ($beforeHash -ne $afterHash) { throw "Unexpected decoded-pixel change in row$row" }
            Write-Output "row$row unchanged"
        }
    }

    for ($frame = 0; $frame -lt 6; $frame++) {
        $cellHash = Get-RectHash $after ([System.Drawing.Rectangle]::new($frame * 256, $targetRow * 256, 256, 256))
        $sprite = [System.Drawing.Bitmap]::new((Join-Path $FrameDirectory ('sequence_NE_{0}.png' -f $frame)))
        try { $spriteHash = Get-RectHash $sprite ([System.Drawing.Rectangle]::new(0, 0, 256, 256)) }
        finally { $sprite.Dispose() }
        if ($cellHash -ne $spriteHash) { throw "NE frame $frame differs after composition." }
        Write-Output "NE frame$frame exact"
    }
}
finally { $before.Dispose(); $after.Dispose() }

Get-Item -LiteralPath $CandidatePath | Select-Object FullName,Length,LastWriteTime
