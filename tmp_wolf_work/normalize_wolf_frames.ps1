$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$generatedRoot = 'C:\Users\hrin2\.codex\generated_images\01a1a5a8-6811-7c93-a543-536793c4de93'
$outputRoot = $PSScriptRoot

$targets = @{
    'SE' = [System.Drawing.Rectangle]::new(62, 67, 132, 171)
    'E'  = [System.Drawing.Rectangle]::new(26, 107, 204, 131)
    'NE' = [System.Drawing.Rectangle]::new(38, 77, 180, 161)
    'N'  = [System.Drawing.Rectangle]::new(73, 57, 110, 181)
}

$specs = @(
    [pscustomobject]@{ Dir='SE'; Frame=0; File='exec-32c7134c-e8fc-44a1-84d5-18278bbb2e22.png'; X=271; Y=413; W=681; H=692 },
    [pscustomobject]@{ Dir='SE'; Frame=1; File='exec-a4e54d20-8243-48f3-baca-93153c0ce66b.png'; X=265; Y=414; W=689; H=679 },
    [pscustomobject]@{ Dir='SE'; Frame=2; File='exec-f408e652-ca36-48e0-acd2-2f6162ed7b81.png'; X=263; Y=403; W=691; H=604 },
    [pscustomobject]@{ Dir='SE'; Frame=3; File='exec-59235592-a47b-4fc5-bca0-e241b9e25f70.png'; X=252; Y=415; W=700; H=683 },
    [pscustomobject]@{ Dir='SE'; Frame=4; File='exec-fbe7e0b2-f483-4a4e-8604-9492f3ce109e.png'; X=272; Y=411; W=682; H=664 },
    [pscustomobject]@{ Dir='SE'; Frame=5; File='exec-11a0b5d0-b432-4ab4-9213-7ced4b1d9a8f.png'; X=267; Y=421; W=687; H=624 },

    [pscustomobject]@{ Dir='E'; Frame=0; File='exec-aedd9eac-9767-4f29-9f07-27660b7e3992.png'; X=161; Y=442; W=936; H=560 },
    [pscustomobject]@{ Dir='E'; Frame=1; File='exec-68bc259f-51ca-406b-a93b-94fa65854993.png'; X=215; Y=214; W=1107; H=635 },
    [pscustomobject]@{ Dir='E'; Frame=2; File='exec-0b9cee75-4d13-4006-b43a-a3846f43818b.png'; X=232; Y=213; W=1076; H=616 },
    [pscustomobject]@{ Dir='E'; Frame=3; File='exec-8ab442cf-e0d4-45a6-840a-41cdb0466a17.png'; X=230; Y=260; W=1049; H=566 },
    [pscustomobject]@{ Dir='E'; Frame=4; File='exec-bc97fc23-fde9-4372-b3ae-5dba9fda61fe.png'; X=300; Y=259; W=957; H=553 },
    [pscustomobject]@{ Dir='E'; Frame=5; File='exec-6646cd05-d388-4dba-9bbe-06f586d27d0b.png'; X=252; Y=241; W=1048; H=582 },

    [pscustomobject]@{ Dir='NE'; Frame=0; File='exec-92c0b8ed-7f03-4f1c-839f-ed3646a971c3.png'; X=190; Y=328; W=903; H=709 },
    [pscustomobject]@{ Dir='NE'; Frame=1; File='exec-4345ccf3-8324-49c9-9ead-4271c14b574f.png'; X=313; Y=162; W=930; H=716 },
    [pscustomobject]@{ Dir='NE'; Frame=2; File='exec-5cf23d7a-123f-4df8-822b-c335eb625f74.png'; X=180; Y=325; W=909; H=697 },
    [pscustomobject]@{ Dir='NE'; Frame=3; File='exec-54b14de5-e1cf-43cd-9b04-019e7f8b54bc.png'; X=187; Y=328; W=905; H=704 },
    [pscustomobject]@{ Dir='NE'; Frame=4; File='exec-f43fbc77-a47d-4d65-9fcb-b02633126b7e.png'; X=198; Y=330; W=894; H=669 },
    [pscustomobject]@{ Dir='NE'; Frame=5; File='exec-c829bc6a-c8c1-4247-869a-484dbe4b7e74.png'; X=171; Y=327; W=921; H=697 },

    [pscustomobject]@{ Dir='N'; Frame=0; File='exec-58875b32-9e44-45ad-85e3-eac7a3f040c4.png'; X=373; Y=185; W=450; H=852 },
    [pscustomobject]@{ Dir='N'; Frame=1; File='exec-9e302e50-8d58-4a85-bad0-9b515eb53b59.png'; X=358; Y=184; W=465; H=804 },
    [pscustomobject]@{ Dir='N'; Frame=2; File='exec-814ec4b3-6ef2-4919-99cd-652ce5bf5576.png'; X=364; Y=178; W=454; H=844 },
    [pscustomobject]@{ Dir='N'; Frame=3; File='exec-eaa8c45b-0005-4a95-a9a1-831be27909a5.png'; X=315; Y=195; W=479; H=893 },
    [pscustomobject]@{ Dir='N'; Frame=4; File='exec-949909c3-d0b9-470b-b92a-9ea14adb2838.png'; X=358; Y=181; W=463; H=855 },
    [pscustomobject]@{ Dir='N'; Frame=5; File='exec-6ae1c771-e704-402c-a3c1-646904b214a5.png'; X=306; Y=192; W=496; H=909 }
)

function Convert-Frame {
    param([pscustomobject]$Spec)

    $sourcePath = Join-Path $generatedRoot $Spec.File
    $source = [System.Drawing.Bitmap]::FromFile($sourcePath)
    try {
        $result = [System.Drawing.Bitmap]::new(256, 256, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
        try {
            $graphics = [System.Drawing.Graphics]::FromImage($result)
            try {
                $graphics.Clear([System.Drawing.Color]::Transparent)
                $graphics.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceCopy
                $graphics.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
                $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
                $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
                $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
                $sourceRect = [System.Drawing.Rectangle]::new($Spec.X, $Spec.Y, $Spec.W, $Spec.H)
                $graphics.DrawImage($source, $targets[$Spec.Dir], $sourceRect, [System.Drawing.GraphicsUnit]::Pixel)
            }
            finally {
                $graphics.Dispose()
            }

            $count = 0
            $sumR = [long]0
            $sumG = [long]0
            $sumB = [long]0
            for ($y = 0; $y -lt 256; $y++) {
                for ($x = 0; $x -lt 256; $x++) {
                    $color = $result.GetPixel($x, $y)
                    if ($color.A -ge 64) {
                        $count++
                        $sumR += $color.R
                        $sumG += $color.G
                        $sumB += $color.B
                    }
                }
            }

            $multR = 106.0 / ($sumR / [double]$count)
            $multG = 97.0 / ($sumG / [double]$count)
            $multB = 91.0 / ($sumB / [double]$count)
            for ($y = 0; $y -lt 256; $y++) {
                for ($x = 0; $x -lt 256; $x++) {
                    $color = $result.GetPixel($x, $y)
                    if ($color.A -gt 0) {
                        $r = [math]::Min(255, [math]::Round($color.R * $multR))
                        $g = [math]::Min(255, [math]::Round($color.G * $multG))
                        $b = [math]::Min(255, [math]::Round($color.B * $multB))
                        $result.SetPixel($x, $y, [System.Drawing.Color]::FromArgb($color.A, [int]$r, [int]$g, [int]$b))
                    }
                }
            }

            $outputPath = Join-Path $outputRoot ('final_{0}_{1}.png' -f $Spec.Dir, $Spec.Frame)
            $result.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png)
        }
        finally {
            $result.Dispose()
        }
    }
    finally {
        $source.Dispose()
    }
}

foreach ($spec in $specs) {
    Convert-Frame -Spec $spec
}

$nwTarget = [System.Drawing.Rectangle]::new(48, 72, 160, 166)
for ($frame = 0; $frame -lt 6; $frame++) {
    $ne = [System.Drawing.Bitmap]::FromFile((Join-Path $outputRoot ('final_NE_{0}.png' -f $frame)))
    try {
        $mirrored = $ne.Clone([System.Drawing.Rectangle]::new(0, 0, 256, 256), [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
        try {
            $mirrored.RotateFlip([System.Drawing.RotateFlipType]::RotateNoneFlipX)
            $nw = [System.Drawing.Bitmap]::new(256, 256, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
            try {
                $graphics = [System.Drawing.Graphics]::FromImage($nw)
                try {
                    $graphics.Clear([System.Drawing.Color]::Transparent)
                    $graphics.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceCopy
                    $graphics.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
                    $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
                    $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
                    $graphics.DrawImage($mirrored, $nwTarget, [System.Drawing.Rectangle]::new(38, 77, 180, 161), [System.Drawing.GraphicsUnit]::Pixel)
                }
                finally {
                    $graphics.Dispose()
                }
                $nw.Save((Join-Path $outputRoot ('final_NW_{0}.png' -f $frame)), [System.Drawing.Imaging.ImageFormat]::Png)
            }
            finally {
                $nw.Dispose()
            }
        }
        finally {
            $mirrored.Dispose()
        }
    }
    finally {
        $ne.Dispose()
    }
}

Get-ChildItem -LiteralPath $outputRoot -Filter 'final_*.png' | Sort-Object Name | Select-Object Name, Length
