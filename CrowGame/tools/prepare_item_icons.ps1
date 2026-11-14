$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing

if(-not ('CrowGameIconPrep' -as [type])){
    Add-Type -ReferencedAssemblies @(
        [System.Drawing.Bitmap].Assembly.Location,
        [System.Drawing.Rectangle].Assembly.Location
    ) -TypeDefinition @'
using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;

public static class CrowGameIconPrep
{
    public static Rectangle CleanAndGetBounds(Bitmap bitmap, byte alphaThreshold)
    {
        Rectangle full = new Rectangle(0, 0, bitmap.Width, bitmap.Height);
        BitmapData data = bitmap.LockBits(full, ImageLockMode.ReadWrite, PixelFormat.Format32bppArgb);
        try
        {
            int stride = Math.Abs(data.Stride);
            byte[] pixels = new byte[stride * bitmap.Height];
            Marshal.Copy(data.Scan0, pixels, 0, pixels.Length);
            int minX = bitmap.Width, minY = bitmap.Height, maxX = -1, maxY = -1;

            for (int y = 0; y < bitmap.Height; y++)
            {
                int row = data.Stride >= 0 ? y * data.Stride : (bitmap.Height - 1 - y) * stride;
                for (int x = 0; x < bitmap.Width; x++)
                {
                    int offset = row + x * 4;
                    byte alpha = pixels[offset + 3];
                    if (alpha < alphaThreshold)
                    {
                        pixels[offset] = pixels[offset + 1] = pixels[offset + 2] = pixels[offset + 3] = 0;
                        continue;
                    }

                    if (x < minX) minX = x;
                    if (x > maxX) maxX = x;
                    if (y < minY) minY = y;
                    if (y > maxY) maxY = y;
                }
            }

            Marshal.Copy(pixels, 0, data.Scan0, pixels.Length);
            return maxX < 0
                ? Rectangle.Empty
                : new Rectangle(minX, minY, maxX - minX + 1, maxY - minY + 1);
        }
        finally
        {
            bitmap.UnlockBits(data);
        }
    }

    public static int CountDirtyTransparent(Bitmap bitmap)
    {
        Rectangle full = new Rectangle(0, 0, bitmap.Width, bitmap.Height);
        BitmapData data = bitmap.LockBits(full, ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb);
        try
        {
            int stride = Math.Abs(data.Stride);
            byte[] pixels = new byte[stride * bitmap.Height];
            Marshal.Copy(data.Scan0, pixels, 0, pixels.Length);
            int dirty = 0;
            for (int y = 0; y < bitmap.Height; y++)
            {
                int row = data.Stride >= 0 ? y * data.Stride : (bitmap.Height - 1 - y) * stride;
                for (int x = 0; x < bitmap.Width; x++)
                {
                    int offset = row + x * 4;
                    if (pixels[offset + 3] == 0 &&
                        (pixels[offset] != 0 || pixels[offset + 1] != 0 || pixels[offset + 2] != 0)) dirty++;
                }
            }
            return dirty;
        }
        finally
        {
            bitmap.UnlockBits(data);
        }
    }

    public static int CountVisibleEdgePixels(Bitmap bitmap, byte alphaThreshold)
    {
        int count = 0;
        for (int x = 0; x < bitmap.Width; x++)
        {
            if (bitmap.GetPixel(x, 0).A >= alphaThreshold) count++;
            if (bitmap.GetPixel(x, bitmap.Height - 1).A >= alphaThreshold) count++;
        }
        for (int y = 1; y < bitmap.Height - 1; y++)
        {
            if (bitmap.GetPixel(0, y).A >= alphaThreshold) count++;
            if (bitmap.GetPixel(bitmap.Width - 1, y).A >= alphaThreshold) count++;
        }
        return count;
    }
}
'@
}

$project=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$assetDir=Join-Path $project 'assets'
$generatedDir=Join-Path $project 'generated'
$outputDir=Join-Path $generatedDir 'icons'
[System.IO.Directory]::CreateDirectory($outputDir)|Out-Null

$items=@(
    'wooden sword.png',
    'Stone Sword.png',
    'fishing rod.png',
    'torchlight.png',
    'Wooden Pickaxe.png',
    'stone pickaxe.png',
    'wooden ax.png',
    'stone ax.png',
    'Wooden Spear.png',
    'Stone Spear.png',
    'Light armor.png',
    'wood.png',
    'stone.png',
    'fiber.png',
    'travel bedding set.png'
)

$transparent=[System.Drawing.Color]::FromArgb(0,0,0,0)
$thumbSize=160
$padding=10
$results=@()

foreach($name in $items){
    $sourcePath=Join-Path $assetDir $name
    if(-not (Test-Path -LiteralPath $sourcePath)){throw "Missing item asset: $sourcePath"}
    $loaded=[System.Drawing.Bitmap]::new($sourcePath)
    try{
        $source=[System.Drawing.Bitmap]::new($loaded.Width,$loaded.Height,[System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
        try{
            $g=[System.Drawing.Graphics]::FromImage($source)
            try{
                $g.CompositingMode=[System.Drawing.Drawing2D.CompositingMode]::SourceCopy
                $g.Clear($transparent)
                $g.DrawImageUnscaled($loaded,0,0)
            }finally{$g.Dispose()}

            $threshold=if($name -eq 'fishing rod.png'){96}else{16}
            $bounds=[CrowGameIconPrep]::CleanAndGetBounds($source,[byte]$threshold)
            if($bounds.IsEmpty){throw "No visible pixels after cleaning: $name"}

            $available=$thumbSize-($padding*2)
            $scale=[Math]::Min($available/$bounds.Width,$available/$bounds.Height)
            $width=[Math]::Max(1,[int][Math]::Round($bounds.Width*$scale))
            $height=[Math]::Max(1,[int][Math]::Round($bounds.Height*$scale))
            $x=[int][Math]::Round(($thumbSize-$width)/2.0)
            $y=[int][Math]::Round(($thumbSize-$height)/2.0)

            $thumb=[System.Drawing.Bitmap]::new($thumbSize,$thumbSize,[System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
            try{
                $g=[System.Drawing.Graphics]::FromImage($thumb)
                try{
                    $g.CompositingMode=[System.Drawing.Drawing2D.CompositingMode]::SourceCopy
                    $g.CompositingQuality=[System.Drawing.Drawing2D.CompositingQuality]::HighQuality
                    $g.InterpolationMode=[System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
                    $g.PixelOffsetMode=[System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
                    $g.SmoothingMode=[System.Drawing.Drawing2D.SmoothingMode]::HighQuality
                    $g.Clear($transparent)
                    $g.DrawImage($source,[System.Drawing.Rectangle]::new($x,$y,$width,$height),$bounds,[System.Drawing.GraphicsUnit]::Pixel)
                }finally{$g.Dispose()}

                # Remove bicubic fringe with imperceptible alpha while keeping antialiased edges.
                $finalBounds=[CrowGameIconPrep]::CleanAndGetBounds($thumb,[byte]3)
                $outputPath=Join-Path $outputDir $name
                $thumb.Save($outputPath,[System.Drawing.Imaging.ImageFormat]::Png)
                $results+=[pscustomobject]@{
                    Name=$name
                    SourceBounds=('{0},{1},{2},{3}' -f $bounds.X,$bounds.Y,$bounds.Width,$bounds.Height)
                    FinalBounds=('{0},{1},{2},{3}' -f $finalBounds.X,$finalBounds.Y,$finalBounds.Width,$finalBounds.Height)
                    EdgePixels=[CrowGameIconPrep]::CountVisibleEdgePixels($thumb,[byte]3)
                    DirtyTransparent=[CrowGameIconPrep]::CountDirtyTransparent($thumb)
                    Bytes=(Get-Item -LiteralPath $outputPath).Length
                }
            }finally{$thumb.Dispose()}
        }finally{$source.Dispose()}
    }finally{$loaded.Dispose()}
}

# A compact QA contact sheet lives outside the icons directory so that the
# runtime folder contains exactly the fifteen usable item thumbnails.
$previewPath=Join-Path $generatedDir 'item_icons_preview.png'
$cellWidth=190;$cellHeight=205
$preview=[System.Drawing.Bitmap]::new($cellWidth*5,$cellHeight*3,[System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
try{
    $g=[System.Drawing.Graphics]::FromImage($preview)
    try{
        $g.Clear([System.Drawing.Color]::FromArgb(255,29,24,22))
        $font=[System.Drawing.Font]::new('Segoe UI',11,[System.Drawing.FontStyle]::Bold)
        try{
            for($index=0;$index -lt $items.Count;$index++){
                $column=$index%5;$row=[Math]::Floor($index/5)
                $left=$column*$cellWidth;$top=$row*$cellHeight
                $g.FillRectangle([System.Drawing.Brushes]::Black,$left+14,$top+10,162,162)
                $icon=[System.Drawing.Bitmap]::new((Join-Path $outputDir $items[$index]))
                try{$g.DrawImageUnscaled($icon,$left+15,$top+11)}finally{$icon.Dispose()}
                $g.DrawString($items[$index],$font,[System.Drawing.Brushes]::White,$left+8,$top+176)
            }
        }finally{$font.Dispose()}
    }finally{$g.Dispose()}
    $preview.Save($previewPath,[System.Drawing.Imaging.ImageFormat]::Png)
}finally{$preview.Dispose()}

$results|Format-Table -AutoSize
Write-Output ('Generated {0} item thumbnails in {1}' -f $items.Count,$outputDir)
Write-Output ('Preview: {0}' -f $previewPath)
