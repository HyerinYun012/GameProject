$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

if (-not ('WolfNPixelPrep' -as [type])) {
    Add-Type -ReferencedAssemblies @(
        [System.Drawing.Bitmap].Assembly.Location,
        [System.Drawing.Rectangle].Assembly.Location
    ) -TypeDefinition @'
using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;
public static class WolfNPixelPrep
{
    public static Rectangle CleanAndGetBounds(Bitmap bitmap, byte alphaThreshold)
    {
        Rectangle rect = new Rectangle(0, 0, bitmap.Width, bitmap.Height);
        BitmapData data = bitmap.LockBits(rect, ImageLockMode.ReadWrite, PixelFormat.Format32bppArgb);
        try
        {
            int stride = Math.Abs(data.Stride);
            byte[] p = new byte[stride * bitmap.Height];
            Marshal.Copy(data.Scan0, p, 0, p.Length);
            int minX=bitmap.Width,minY=bitmap.Height,maxX=-1,maxY=-1;
            for(int y=0;y<bitmap.Height;y++)
            {
                int row=data.Stride>=0?y*data.Stride:(bitmap.Height-1-y)*stride;
                for(int x=0;x<bitmap.Width;x++)
                {
                    int o=row+x*4;
                    if(p[o+3]<alphaThreshold){p[o]=p[o+1]=p[o+2]=p[o+3]=0;}
                    else {p[o+3]=255;if(x<minX)minX=x;if(x>maxX)maxX=x;if(y<minY)minY=y;if(y>maxY)maxY=y;}
                }
            }
            Marshal.Copy(p,0,data.Scan0,p.Length);
            return maxX<0?Rectangle.Empty:new Rectangle(minX,minY,maxX-minX+1,maxY-minY+1);
        }
        finally { bitmap.UnlockBits(data); }
    }
}
'@
}

$transparentBlack=[System.Drawing.Color]::FromArgb(0,0,0,0)
$outputPrefix='sequence_N_v3_'
$previewName='preview_sequence_N_v3.png'
$sourceNames=@(
    'individual_N_F0_raw.png',
    'individual_N_F1_locked_raw.png',
    'individual_N_F2_locked_raw.png',
    'individual_N_F3_locked_raw.png',
    'individual_N_F4_locked_raw.png',
    'individual_N_F5_locked_raw.png'
)
$sources=@();$boundsList=@();$maxWidth=0;$maxHeight=0
$zoomFactors=@(1.0,1.0,1.0,1.0,1.0,1.0)

try {
    for($frame=0;$frame -lt 6;$frame++){
        $path=Resolve-Path (Join-Path $PSScriptRoot $sourceNames[$frame])
        $bitmap=[System.Drawing.Bitmap]::new($path.Path)
        $bounds=[WolfNPixelPrep]::CleanAndGetBounds($bitmap,96)
        if($bounds.IsEmpty){$bitmap.Dispose();throw "No wolf pixels in frame $frame"}
        $sources+=$bitmap;$boundsList+=$bounds
        if($bounds.Width -gt $maxWidth){$maxWidth=$bounds.Width}
        if($bounds.Height -gt $maxHeight){$maxHeight=$bounds.Height}
    }

    $frames=@()
    for($frame=0;$frame -lt 6;$frame++){
        $source=$sources[$frame];$bounds=$boundsList[$frame]
        # Keep the non-leg mass motionless: every cleaned frame occupies the
        # same box and pivot.  The generated variants differ slightly in raw
        # camera scale, so a shared scale factor would make the head bob.
        $width=76;$height=171;$dx=90;$dy=67
        $out=[System.Drawing.Bitmap]::new(256,256,[System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
        $g=[System.Drawing.Graphics]::FromImage($out)
        try{
            $g.CompositingMode=[System.Drawing.Drawing2D.CompositingMode]::SourceCopy
            $g.CompositingQuality=[System.Drawing.Drawing2D.CompositingQuality]::HighQuality
            $g.InterpolationMode=[System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
            $g.PixelOffsetMode=[System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
            $g.Clear($transparentBlack)
            $g.DrawImage($source,[System.Drawing.Rectangle]::new($dx,$dy,$width,$height),$bounds,[System.Drawing.GraphicsUnit]::Pixel)
        }finally{$g.Dispose()}

        [long]$sr=0;[long]$sg=0;[long]$sb=0;[long]$count=0
        for($y=0;$y -lt 256;$y++){for($x=0;$x -lt 256;$x++){
            $c=$out.GetPixel($x,$y)
            if($c.A -lt 16){$out.SetPixel($x,$y,$transparentBlack);continue}
            if($c.A -ge 64){$sr+=$c.R;$sg+=$c.G;$sb+=$c.B;$count++}
        }}
        $dr=97-[int]($sr/$count);$dg=88-[int]($sg/$count);$db=82-[int]($sb/$count)
        for($y=0;$y -lt 256;$y++){for($x=0;$x -lt 256;$x++){
            $c=$out.GetPixel($x,$y)
            if($c.A -lt 16){$out.SetPixel($x,$y,$transparentBlack);continue}
            $r=[Math]::Max(0,[Math]::Min(255,$c.R+$dr));$green=[Math]::Max(0,[Math]::Min(255,$c.G+$dg));$b=[Math]::Max(0,[Math]::Min(255,$c.B+$db))
            $out.SetPixel($x,$y,[System.Drawing.Color]::FromArgb($c.A,$r,$green,$b))
        }}
        $out.Save((Join-Path $PSScriptRoot ('{0}{1}.png' -f $outputPrefix,$frame)),[System.Drawing.Imaging.ImageFormat]::Png)
        $frames+=$out
        Write-Output ('frame{0}: raw={1},{2},{3},{4} dest={5},{6},{7},{8}' -f $frame,$bounds.X,$bounds.Y,$bounds.Width,$bounds.Height,$dx,$dy,$width,$height)
    }

    $preview=[System.Drawing.Bitmap]::new(1536,256,[System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    try{$g=[System.Drawing.Graphics]::FromImage($preview);try{$g.CompositingMode=[System.Drawing.Drawing2D.CompositingMode]::SourceCopy;$g.Clear($transparentBlack);for($f=0;$f -lt 6;$f++){$g.DrawImageUnscaled($frames[$f],$f*256,0)}}finally{$g.Dispose()};$preview.Save((Join-Path $PSScriptRoot $previewName),[System.Drawing.Imaging.ImageFormat]::Png)}finally{$preview.Dispose()}
    foreach($f in $frames){$f.Dispose()}
}finally{foreach($s in $sources){if($s){$s.Dispose()}}}
