$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$scale = 4
$workSize = 1024
$sourcePaths = 0..5 | ForEach-Object { (Resolve-Path (Join-Path $PSScriptRoot ('mirror_SW_to_SE_{0}.png' -f $_))).Path }

# Approximate paw centres measured from the accepted mirrored SW art.
$farForePaws = @(@(128,205), @(151,210), @(165,224), @(145,221), @(181,218), @(183,220))
$nearForePaws = @(@(198,231), @(176,230), @(148,228), @(174,231), @(150,235), @(166,231))

function New-TransparentBitmap([int]$Width, [int]$Height) {
    $bitmap = [System.Drawing.Bitmap]::new($Width, $Height, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $g = [System.Drawing.Graphics]::FromImage($bitmap)
    try {
        $g.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceCopy
        $g.Clear([System.Drawing.Color]::Transparent)
    }
    finally { $g.Dispose() }
    return $bitmap
}

function New-UpscaledSource([string]$Path) {
    $small = [System.Drawing.Bitmap]::new($Path)
    try {
        $large = New-TransparentBitmap $workSize $workSize
        $g = [System.Drawing.Graphics]::FromImage($large)
        try {
            $g.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceCopy
            $g.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
            $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
            $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
            $g.DrawImage($small, [System.Drawing.Rectangle]::new(0,0,$workSize,$workSize), [System.Drawing.Rectangle]::new(0,0,256,256), [System.Drawing.GraphicsUnit]::Pixel)
        }
        finally { $g.Dispose() }
        return $large
    }
    finally { $small.Dispose() }
}

function New-LimbPath([double]$AnchorX, [double]$AnchorY, [double]$PawX, [double]$PawY, [double]$Width) {
    $path = [System.Drawing.Drawing2D.GraphicsPath]::new()
    $path.AddLine([single]($AnchorX*$scale), [single]($AnchorY*$scale), [single]($PawX*$scale), [single]($PawY*$scale))
    $pen = [System.Drawing.Pen]::new([System.Drawing.Color]::White, [single]($Width*$scale))
    try {
        $pen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
        $pen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
        $pen.LineJoin = [System.Drawing.Drawing2D.LineJoin]::Round
        $path.Widen($pen)
    }
    finally { $pen.Dispose() }
    $pawRadiusX = ($Width * 0.58) * $scale
    $pawRadiusY = ($Width * 0.43) * $scale
    $path.AddEllipse([single]($PawX*$scale-$pawRadiusX), [single]($PawY*$scale-$pawRadiusY), [single](2*$pawRadiusX), [single](2*$pawRadiusY))
    return $path
}

function New-BodyPath {
    $coords = @(
        @(43,112), @(54,85), @(82,64), @(118,61), @(152,68), @(183,80), @(202,95), @(211,120),
        @(210,148), @(202,169), @(189,184), @(170,190), @(151,179), @(143,169), @(126,165), @(105,164),
        @(85,162), @(65,163), @(47,153)
    )
    $points = [System.Drawing.PointF[]]::new($coords.Count)
    for ($i=0; $i -lt $coords.Count; $i++) {
        $points[$i] = [System.Drawing.PointF]::new([single]($coords[$i][0]*$scale), [single]($coords[$i][1]*$scale))
    }
    $path = [System.Drawing.Drawing2D.GraphicsPath]::new()
    $path.AddPolygon($points)
    return $path
}

function Extract-WithPath([System.Drawing.Bitmap]$Source, [System.Drawing.Drawing2D.GraphicsPath]$Path) {
    $layer = New-TransparentBitmap $workSize $workSize
    $g = [System.Drawing.Graphics]::FromImage($layer)
    try {
        $g.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceCopy
        $g.SetClip($Path)
        $g.DrawImageUnscaled($Source, 0, 0)
    }
    finally { $g.Dispose() }
    return $layer
}

function Clear-WithPath([System.Drawing.Bitmap]$Bitmap, [System.Drawing.Drawing2D.GraphicsPath]$Path) {
    $g = [System.Drawing.Graphics]::FromImage($Bitmap)
    try {
        $g.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceCopy
        $g.SetClip($Path)
        $clearBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::Transparent)
        try { $g.FillRectangle($clearBrush, 0, 0, $workSize, $workSize) }
        finally { $clearBrush.Dispose() }
    }
    finally { $g.Dispose() }
}

function Get-AlphaBounds([System.Drawing.Bitmap]$Bitmap, [int]$Threshold=16) {
    $minX=$Bitmap.Width; $minY=$Bitmap.Height; $maxX=-1; $maxY=-1
    for($y=0;$y -lt $Bitmap.Height;$y++) {
        for($x=0;$x -lt $Bitmap.Width;$x++) {
            if($Bitmap.GetPixel($x,$y).A -ge $Threshold) {
                if($x -lt $minX){$minX=$x}; if($x -gt $maxX){$maxX=$x}
                if($y -lt $minY){$minY=$y}; if($y -gt $maxY){$maxY=$y}
            }
        }
    }
    if($maxX -lt 0){ throw 'Empty image.' }
    return [System.Drawing.Rectangle]::new($minX,$minY,$maxX-$minX+1,$maxY-$minY+1)
}

$sources = @()
try {
    foreach($path in $sourcePaths){ $sources += New-UpscaledSource $path }

    # Each result uses the body/hind-leg phase from BodyFrame and the opposite
    # foreleg phase from ForeFrame, converting the source trot into a pace.
    $specs = @(
        [pscustomobject]@{BodyFrame=4; ForeFrame=0; Lift=0},
        [pscustomobject]@{BodyFrame=5; ForeFrame=1; Lift=-1},
        [pscustomobject]@{BodyFrame=1; ForeFrame=2; Lift=-2},
        [pscustomobject]@{BodyFrame=0; ForeFrame=4; Lift=0},
        [pscustomobject]@{BodyFrame=1; ForeFrame=2; Lift=-1},
        [pscustomobject]@{BodyFrame=5; ForeFrame=1; Lift=-2}
    )

    $preview = New-TransparentBitmap 1536 256
    try {
        $previewG = [System.Drawing.Graphics]::FromImage($preview)
        try {
            $previewG.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceOver
            for($frame=0;$frame -lt 6;$frame++) {
                $bodyIndex = $specs[$frame].BodyFrame
                $foreIndex = $specs[$frame].ForeFrame
                $bodySource = $sources[$bodyIndex]
                $foreSource = $sources[$foreIndex]

                $baseFarPath = New-LimbPath 145 158 $farForePaws[$bodyIndex][0] $farForePaws[$bodyIndex][1] 18
                $baseNearPath = New-LimbPath 160 159 $nearForePaws[$bodyIndex][0] $nearForePaws[$bodyIndex][1] 22
                $sourceFarPath = New-LimbPath 145 158 $farForePaws[$foreIndex][0] $farForePaws[$foreIndex][1] 18
                $sourceNearPath = New-LimbPath 160 159 $nearForePaws[$foreIndex][0] $nearForePaws[$foreIndex][1] 22
                $bodyPath = New-BodyPath
                try {
                    $composite = $bodySource.Clone([System.Drawing.Rectangle]::new(0,0,$workSize,$workSize), [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
                    try {
                        Clear-WithPath $composite $baseFarPath
                        Clear-WithPath $composite $baseNearPath
                        $farLayer = Extract-WithPath $foreSource $sourceFarPath
                        $nearLayer = Extract-WithPath $foreSource $sourceNearPath
                        $bodyLayer = Extract-WithPath $bodySource $bodyPath
                        try {
                            $g = [System.Drawing.Graphics]::FromImage($composite)
                            try {
                                $g.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceOver
                                $g.DrawImageUnscaled($farLayer, 0, [int]($specs[$frame].Lift*$scale))
                                $g.DrawImageUnscaled($bodyLayer, 0, 0)
                                $g.DrawImageUnscaled($nearLayer, 0, [int]($specs[$frame].Lift*$scale))
                            }
                            finally { $g.Dispose() }

                            $small = New-TransparentBitmap 256 256
                            try {
                                $down = [System.Drawing.Graphics]::FromImage($small)
                                try {
                                    $down.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceCopy
                                    $down.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
                                    $down.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
                                    $down.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
                                    $down.DrawImage($composite, [System.Drawing.Rectangle]::new(0,10,256,256), [System.Drawing.Rectangle]::new(0,0,$workSize,$workSize), [System.Drawing.GraphicsUnit]::Pixel)
                                }
                                finally { $down.Dispose() }

                                for($y=0;$y -lt 256;$y++) { for($x=0;$x -lt 256;$x++) {
                                    $c=$small.GetPixel($x,$y); if($c.A -lt 16){$small.SetPixel($x,$y,[System.Drawing.Color]::Transparent)}
                                }}
                                $outPath = Join-Path $PSScriptRoot ('pace2_SE_{0}.png' -f $frame)
                                $small.Save($outPath,[System.Drawing.Imaging.ImageFormat]::Png)
                                $previewG.DrawImageUnscaled($small,$frame*256,0)
                                $bounds=Get-AlphaBounds $small 16
                                Write-Output ('f{0}: body={1} fore={2} bbox={3},{4},{5},{6} bottom={7}' -f $frame,$bodyIndex,$foreIndex,$bounds.X,$bounds.Y,$bounds.Width,$bounds.Height,($bounds.Bottom-1))
                            }
                            finally { $small.Dispose() }
                        }
                        finally { $farLayer.Dispose(); $nearLayer.Dispose(); $bodyLayer.Dispose() }
                    }
                    finally { $composite.Dispose() }
                }
                finally { $baseFarPath.Dispose(); $baseNearPath.Dispose(); $sourceFarPath.Dispose(); $sourceNearPath.Dispose(); $bodyPath.Dispose() }
            }
        }
        finally { $previewG.Dispose() }
        $preview.Save((Join-Path $PSScriptRoot 'preview_pace2_SE.png'),[System.Drawing.Imaging.ImageFormat]::Png)
    }
    finally { $preview.Dispose() }
}
finally { foreach($source in $sources){ if($null -ne $source){$source.Dispose()} } }
