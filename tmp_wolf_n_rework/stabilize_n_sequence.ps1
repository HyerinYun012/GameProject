$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing

$transparent=[System.Drawing.Color]::FromArgb(0,0,0,0)
$frames=@()

function Get-TailHalfWidth([int]$Y){
    if($Y -lt 166 -or $Y -gt 223){return -1}
    if($Y -le 180){return [int][Math]::Round(10+(($Y-166)*0.43))}
    if($Y -le 196){return [int][Math]::Round(16+(($Y-180)*0.06))}
    if($Y -le 210){return [int][Math]::Round(17-(($Y-196)*0.36))}
    return [Math]::Max(2,[int][Math]::Round(12-(($Y-210)*0.77)))
}

function Blend-Color([System.Drawing.Color]$Pose,[System.Drawing.Color]$Master,[double]$Amount){
    $inv=1.0-$Amount
    $a=[int][Math]::Round(($Pose.A*$inv)+($Master.A*$Amount))
    $r=[int][Math]::Round(($Pose.R*$inv)+($Master.R*$Amount))
    $g=[int][Math]::Round(($Pose.G*$inv)+($Master.G*$Amount))
    $b=[int][Math]::Round(($Pose.B*$inv)+($Master.B*$Amount))
    return [System.Drawing.Color]::FromArgb($a,$r,$g,$b)
}

$masterPath=(Resolve-Path (Join-Path $PSScriptRoot 'sequence_N_v3_0.png')).Path
$master=[System.Drawing.Bitmap]::new($masterPath)
try{
    for($frame=0;$frame -lt 6;$frame++){
        $posePath=(Resolve-Path (Join-Path $PSScriptRoot ('sequence_N_v3_{0}.png' -f $frame))).Path
        $pose=[System.Drawing.Bitmap]::new($posePath)
        try{
            $out=[System.Drawing.Bitmap]::new(256,256,[System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
            for($y=0;$y -lt 256;$y++){
                $tailHalf=Get-TailHalfWidth $y
                for($x=0;$x -lt 256;$x++){
                    $poseColor=$pose.GetPixel($x,$y)
                    $masterColor=$master.GetPixel($x,$y)

                    # Every non-leg pixel is the exact F0 master.  The short
                    # blend band lets the newly posed legs meet the fixed hip
                    # sockets without a visible horizontal seam.
                    if($y -le 170){
                        $color=$masterColor
                    }elseif($y -le 178){
                        $amount=(179-$y)/9.0
                        $color=Blend-Color $poseColor $masterColor $amount
                    }else{
                        $color=$poseColor
                    }

                    # The tail is fixed and drawn in front of the legs.  Copy
                    # the full polygon, including transparent pixels, so a
                    # generated tail cannot protrude or sway outside it.
                    if($tailHalf -ge 0 -and [Math]::Abs($x-128) -le $tailHalf){
                        $color=$masterColor
                    }

                    # Lock the complete visible tail corridor, not only its
                    # centerline.  These bands stay between the four leg
                    # tracks, so the paws remain free while every tail pixel
                    # is byte-identical to F0.
                    $lockTail=$false
                    if($y -ge 171 -and $y -le 185 -and $x -ge 108 -and $x -le 148){$lockTail=$true}
                    elseif($y -ge 186 -and $y -le 205 -and $x -ge 110 -and $x -le 144){$lockTail=$true}
                    elseif($y -ge 206 -and $y -le 215 -and $x -ge 114 -and $x -le 142){$lockTail=$true}
                    elseif($y -ge 216 -and $y -le 223 -and $x -ge 117 -and $x -le 134){$lockTail=$true}
                    if($lockTail){$color=$masterColor}

                    # Generated F2/F3 tails taper several pixels below the
                    # canonical F0 tip.  Scrub only that central corridor;
                    # the row-dependent right edge preserves F0's planted
                    # right paw beginning at x=135/134/133.
                    if($y -ge 224 -and $y -le 232){
                        $tailClearMax=if($y -le 226){134}elseif($y -le 228){133}else{132}
                        if($x -ge 120 -and $x -le $tailClearMax){$color=$transparent}
                    }

                    if($color.A -lt 16){$color=$transparent}
                    $out.SetPixel($x,$y,$color)
                }
            }
            $path=Join-Path $PSScriptRoot ('sequence_N_final_v5_{0}.png' -f $frame)
            $out.Save($path,[System.Drawing.Imaging.ImageFormat]::Png)
            $frames+=$out
        }finally{$pose.Dispose()}
    }

    $preview=[System.Drawing.Bitmap]::new(1536,256,[System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    try{
        $g=[System.Drawing.Graphics]::FromImage($preview)
        try{
            $g.CompositingMode=[System.Drawing.Drawing2D.CompositingMode]::SourceCopy
            $g.Clear($transparent)
            for($f=0;$f -lt 6;$f++){$g.DrawImageUnscaled($frames[$f],$f*256,0)}
        }finally{$g.Dispose()}
        $preview.Save((Join-Path $PSScriptRoot 'preview_sequence_N_final_v5.png'),[System.Drawing.Imaging.ImageFormat]::Png)
    }finally{$preview.Dispose()}
}finally{
    $master.Dispose()
    foreach($frame in $frames){if($frame){$frame.Dispose()}}
}
