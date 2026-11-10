$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Security

$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$sourcePath=Join-Path $root 'Assets\Sprites\Animals\Wolf\wolf_walk.png'
$candidatePath=Join-Path $PSScriptRoot 'wolf_walk_sequence_candidate.png'

function Get-RectHash([System.Drawing.Bitmap]$Bitmap,[System.Drawing.Rectangle]$Rect){
    $clone=$Bitmap.Clone($Rect,[System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    try{
        $data=$clone.LockBits([System.Drawing.Rectangle]::new(0,0,$clone.Width,$clone.Height),[System.Drawing.Imaging.ImageLockMode]::ReadOnly,[System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
        try{
            $length=[Math]::Abs($data.Stride)*$clone.Height
            $bytes=[byte[]]::new($length)
            [System.Runtime.InteropServices.Marshal]::Copy($data.Scan0,$bytes,0,$length)
        }finally{$clone.UnlockBits($data)}
        $sha=[System.Security.Cryptography.SHA256]::Create()
        try{return [Convert]::ToHexString($sha.ComputeHash($bytes))}
        finally{$sha.Dispose()}
    }finally{$clone.Dispose()}
}

function Copy-BitmapCellExact([System.Drawing.Bitmap]$Source,[System.Drawing.Bitmap]$Destination,[int]$DestinationX,[int]$DestinationY){
    $sourceData=$Source.LockBits([System.Drawing.Rectangle]::new(0,0,256,256),[System.Drawing.Imaging.ImageLockMode]::ReadOnly,[System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    try{
        $destinationData=$Destination.LockBits([System.Drawing.Rectangle]::new($DestinationX,$DestinationY,256,256),[System.Drawing.Imaging.ImageLockMode]::WriteOnly,[System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
        try{
            $rowBytes=256*4
            $buffer=[byte[]]::new($rowBytes)
            for($y=0;$y -lt 256;$y++){
                $sourceRow=[IntPtr]::Add($sourceData.Scan0,$y*$sourceData.Stride)
                $destinationRow=[IntPtr]::Add($destinationData.Scan0,$y*$destinationData.Stride)
                [System.Runtime.InteropServices.Marshal]::Copy($sourceRow,$buffer,0,$rowBytes)
                [System.Runtime.InteropServices.Marshal]::Copy($buffer,0,$destinationRow,$rowBytes)
            }
        }finally{$Destination.UnlockBits($destinationData)}
    }finally{$Source.UnlockBits($sourceData)}
}

$loaded=[System.Drawing.Bitmap]::new($sourcePath)
try{
    if($loaded.Width -ne 1536 -or $loaded.Height -ne 2048){throw "Unexpected wolf_walk size: $($loaded.Width)x$($loaded.Height)"}
    $candidate=$loaded.Clone([System.Drawing.Rectangle]::new(0,0,$loaded.Width,$loaded.Height),[System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
}finally{$loaded.Dispose()}

try{
    for($frame=0;$frame -lt 6;$frame++){
        $framePath=Join-Path $PSScriptRoot ('sequence_SE_{0}.png' -f $frame)
        $sprite=[System.Drawing.Bitmap]::new($framePath)
        try{
            if($sprite.Width -ne 256 -or $sprite.Height -ne 256){throw "Unexpected frame size: $framePath"}
            Copy-BitmapCellExact $sprite $candidate ($frame*256) 256
        }finally{$sprite.Dispose()}
    }
    $candidate.Save($candidatePath,[System.Drawing.Imaging.ImageFormat]::Png)
}finally{$candidate.Dispose()}

$before=[System.Drawing.Bitmap]::new($sourcePath)
$after=[System.Drawing.Bitmap]::new($candidatePath)
try{
    for($row=0;$row -lt 8;$row++){
        $rect=[System.Drawing.Rectangle]::new(0,$row*256,1536,256)
        $beforeHash=Get-RectHash $before $rect
        $afterHash=Get-RectHash $after $rect
        if($row -eq 1){
            if($beforeHash -eq $afterHash){throw 'SE row did not change.'}
            Write-Output "row$row changed (expected)"
        }else{
            if($beforeHash -ne $afterHash){throw "Unexpected decoded pixel change in row$row"}
            Write-Output "row$row unchanged"
        }
    }

    for($frame=0;$frame -lt 6;$frame++){
        $cellHash=Get-RectHash $after ([System.Drawing.Rectangle]::new($frame*256,256,256,256))
        $sprite=[System.Drawing.Bitmap]::new((Join-Path $PSScriptRoot ('sequence_SE_{0}.png' -f $frame)))
        try{$spriteHash=Get-RectHash $sprite ([System.Drawing.Rectangle]::new(0,0,256,256))}
        finally{$sprite.Dispose()}
        if($cellHash -ne $spriteHash){throw "SE frame $frame differs after composition."}
        Write-Output "SE frame$frame exact"
    }
}finally{$before.Dispose();$after.Dispose()}

Get-Item -LiteralPath $candidatePath | Select-Object FullName,Length,LastWriteTime
