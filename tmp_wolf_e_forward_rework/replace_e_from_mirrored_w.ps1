param(
    [string]$SourcePath = (Join-Path (Resolve-Path (Join-Path $PSScriptRoot '..')).Path 'Assets\Sprites\Animals\Wolf\wolf_walk.png'),
    [string]$CandidatePath = (Join-Path $PSScriptRoot 'wolf_walk_e_from_mirrored_w_candidate.png'),
    [string]$PreviewPath = (Join-Path $PSScriptRoot 'preview_w_original_e_mirrored.png'),
    [int]$TargetRow = 2,
    [int]$MirrorSourceRow = 6,
    [string]$TargetLabel = 'E',
    [string]$MirrorSourceLabel = 'W'
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Security

$cellSize = 256
$frameCount = 6
$eastRow = $TargetRow
$westRow = $MirrorSourceRow

function Get-RectHash([System.Drawing.Bitmap]$Bitmap, [System.Drawing.Rectangle]$Rect) {
    $clone = $Bitmap.Clone($Rect, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    try {
        $data = $clone.LockBits(
            [System.Drawing.Rectangle]::new(0, 0, $clone.Width, $clone.Height),
            [System.Drawing.Imaging.ImageLockMode]::ReadOnly,
            [System.Drawing.Imaging.PixelFormat]::Format32bppArgb
        )
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

function Copy-MirroredCellExact(
    [System.Drawing.Bitmap]$Source,
    [System.Drawing.Bitmap]$Destination,
    [int]$SourceX,
    [int]$SourceY,
    [int]$DestinationX,
    [int]$DestinationY
) {
    $sourceData = $Source.LockBits(
        [System.Drawing.Rectangle]::new($SourceX, $SourceY, 256, 256),
        [System.Drawing.Imaging.ImageLockMode]::ReadOnly,
        [System.Drawing.Imaging.PixelFormat]::Format32bppArgb
    )
    try {
        $destinationData = $Destination.LockBits(
            [System.Drawing.Rectangle]::new($DestinationX, $DestinationY, 256, 256),
            [System.Drawing.Imaging.ImageLockMode]::WriteOnly,
            [System.Drawing.Imaging.PixelFormat]::Format32bppArgb
        )
        try {
            $rowBytes = 256 * 4
            $sourceRow = [byte[]]::new($rowBytes)
            $mirroredRow = [byte[]]::new($rowBytes)
            for ($y = 0; $y -lt 256; $y++) {
                $sourcePointer = [IntPtr]::Add($sourceData.Scan0, $y * $sourceData.Stride)
                [System.Runtime.InteropServices.Marshal]::Copy($sourcePointer, $sourceRow, 0, $rowBytes)
                for ($x = 0; $x -lt 256; $x++) {
                    $sourceOffset = (255 - $x) * 4
                    $destinationOffset = $x * 4
                    $mirroredRow[$destinationOffset] = $sourceRow[$sourceOffset]
                    $mirroredRow[$destinationOffset + 1] = $sourceRow[$sourceOffset + 1]
                    $mirroredRow[$destinationOffset + 2] = $sourceRow[$sourceOffset + 2]
                    $mirroredRow[$destinationOffset + 3] = $sourceRow[$sourceOffset + 3]
                }
                $destinationPointer = [IntPtr]::Add($destinationData.Scan0, $y * $destinationData.Stride)
                [System.Runtime.InteropServices.Marshal]::Copy($mirroredRow, 0, $destinationPointer, $rowBytes)
            }
        }
        finally { $Destination.UnlockBits($destinationData) }
    }
    finally { $Source.UnlockBits($sourceData) }
}

function Assert-CellIsExactMirror(
    [System.Drawing.Bitmap]$Source,
    [System.Drawing.Bitmap]$Candidate,
    [int]$Frame
) {
    $sourceRect = [System.Drawing.Rectangle]::new($Frame * 256, $westRow * 256, 256, 256)
    $candidateRect = [System.Drawing.Rectangle]::new($Frame * 256, $eastRow * 256, 256, 256)
    $sourceData = $Source.LockBits($sourceRect, [System.Drawing.Imaging.ImageLockMode]::ReadOnly, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    try {
        $candidateData = $Candidate.LockBits($candidateRect, [System.Drawing.Imaging.ImageLockMode]::ReadOnly, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
        try {
            $rowBytes = 256 * 4
            $sourceRow = [byte[]]::new($rowBytes)
            $candidateRow = [byte[]]::new($rowBytes)
            for ($y = 0; $y -lt 256; $y++) {
                [System.Runtime.InteropServices.Marshal]::Copy([IntPtr]::Add($sourceData.Scan0, $y * $sourceData.Stride), $sourceRow, 0, $rowBytes)
                [System.Runtime.InteropServices.Marshal]::Copy([IntPtr]::Add($candidateData.Scan0, $y * $candidateData.Stride), $candidateRow, 0, $rowBytes)
                for ($x = 0; $x -lt 256; $x++) {
                    $sourceOffset = (255 - $x) * 4
                    $candidateOffset = $x * 4
                    for ($channel = 0; $channel -lt 4; $channel++) {
                        if ($candidateRow[$candidateOffset + $channel] -ne $sourceRow[$sourceOffset + $channel]) {
                            throw "$TargetLabel frame $Frame is not an exact horizontal mirror of $MirrorSourceLabel at x=$x y=$y channel=$channel"
                        }
                    }
                }
            }
        }
        finally { $Candidate.UnlockBits($candidateData) }
    }
    finally { $Source.UnlockBits($sourceData) }
}

$source = [System.Drawing.Bitmap]::new((Resolve-Path $SourcePath).Path)
try {
    if ($source.Width -ne 1536 -or $source.Height -ne 2048) {
        throw "Unexpected wolf_walk size: $($source.Width)x$($source.Height)"
    }
    $candidate = $source.Clone(
        [System.Drawing.Rectangle]::new(0, 0, $source.Width, $source.Height),
        [System.Drawing.Imaging.PixelFormat]::Format32bppArgb
    )
    try {
        for ($frame = 0; $frame -lt $frameCount; $frame++) {
            Copy-MirroredCellExact $source $candidate ($frame * $cellSize) ($westRow * $cellSize) ($frame * $cellSize) ($eastRow * $cellSize)
        }
        $candidate.Save($CandidatePath, [System.Drawing.Imaging.ImageFormat]::Png)

        for ($row = 0; $row -lt 8; $row++) {
            $rect = [System.Drawing.Rectangle]::new(0, $row * $cellSize, 1536, 256)
            $beforeHash = Get-RectHash $source $rect
            $afterHash = Get-RectHash $candidate $rect
            if ($row -eq $eastRow) {
                if ($beforeHash -eq $afterHash) { throw "$TargetLabel row did not change." }
                Write-Output "row$row $TargetLabel changed (expected)"
            }
            else {
                if ($beforeHash -ne $afterHash) { throw "Unexpected decoded-pixel change in row$row" }
                Write-Output "row$row unchanged"
            }
        }

        for ($frame = 0; $frame -lt $frameCount; $frame++) {
            Assert-CellIsExactMirror $source $candidate $frame
            Write-Output "$TargetLabel frame$frame is exact mirror of $MirrorSourceLabel frame$frame"
        }

        $preview = [System.Drawing.Bitmap]::new(1536, 512, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
        try {
            $graphics = [System.Drawing.Graphics]::FromImage($preview)
            try {
                $graphics.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceCopy
                $graphics.Clear([System.Drawing.Color]::Transparent)
                $graphics.DrawImage($source, [System.Drawing.Rectangle]::new(0, 0, 1536, 256), [System.Drawing.Rectangle]::new(0, $westRow * 256, 1536, 256), [System.Drawing.GraphicsUnit]::Pixel)
                $graphics.DrawImage($candidate, [System.Drawing.Rectangle]::new(0, 256, 1536, 256), [System.Drawing.Rectangle]::new(0, $eastRow * 256, 1536, 256), [System.Drawing.GraphicsUnit]::Pixel)
            }
            finally { $graphics.Dispose() }
            $preview.Save($PreviewPath, [System.Drawing.Imaging.ImageFormat]::Png)
        }
        finally { $preview.Dispose() }
    }
    finally { $candidate.Dispose() }
}
finally { $source.Dispose() }

Get-Item -LiteralPath $CandidatePath, $PreviewPath | Select-Object FullName, Length, LastWriteTime
