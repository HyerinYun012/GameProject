$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

function New-ContactOverlay {
    param(
        [string]$SourceName,
        [string]$OutputName,
        [System.Drawing.Point[][]]$RedPair,
        [System.Drawing.Point[][]]$BluePair,
        [string]$Title
    )

    $sourcePath = Resolve-Path (Join-Path $PSScriptRoot $SourceName)
    $outputPath = Join-Path $PSScriptRoot $OutputName
    $source = [System.Drawing.Bitmap]::new($sourcePath.Path)
    $canvas = [System.Drawing.Bitmap]::new($source.Width, $source.Height, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $graphics = [System.Drawing.Graphics]::FromImage($canvas)
    try {
        $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
        $graphics.DrawImageUnscaled($source, 0, 0)
        $redPen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(220, 255, 35, 50), 27)
        $bluePen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(220, 25, 145, 255), 23)
        foreach ($pen in @($redPen, $bluePen)) {
            $pen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
            $pen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
        }
        foreach ($line in $RedPair) { $graphics.DrawLines($redPen, $line) }
        foreach ($line in $BluePair) { $graphics.DrawLines($bluePen, $line) }

        $font = [System.Drawing.Font]::new('Arial', 27, [System.Drawing.FontStyle]::Bold)
        $graphics.DrawString($Title, $font, [System.Drawing.Brushes]::LimeGreen, 34, 24)
        $graphics.DrawString('RED = NEAR LEFT FORE + HIND', $font, [System.Drawing.Brushes]::Red, 34, 64)
        $graphics.DrawString('BLUE = FAR RIGHT FORE + HIND', $font, [System.Drawing.Brushes]::DeepSkyBlue, 34, 104)
        $graphics.DrawString('4 ROOTS + 4 PAWS; KEEP LARGE GAPS', $font, [System.Drawing.Brushes]::White, 34, 144)

        $redPen.Dispose(); $bluePen.Dispose(); $font.Dispose()
        $canvas.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png)
    }
    finally {
        $graphics.Dispose(); $canvas.Dispose(); $source.Dispose()
    }
    Write-Output $outputPath
}

$f0Red = @(
    [System.Drawing.Point[]]@([System.Drawing.Point]::new(1040,430),[System.Drawing.Point]::new(1120,570),[System.Drawing.Point]::new(1230,700),[System.Drawing.Point]::new(1350,820)),
    [System.Drawing.Point[]]@([System.Drawing.Point]::new(610,430),[System.Drawing.Point]::new(640,580),[System.Drawing.Point]::new(670,710),[System.Drawing.Point]::new(700,820))
)
$f0Blue = @(
    [System.Drawing.Point[]]@([System.Drawing.Point]::new(960,480),[System.Drawing.Point]::new(930,600),[System.Drawing.Point]::new(910,720),[System.Drawing.Point]::new(900,820)),
    [System.Drawing.Point[]]@([System.Drawing.Point]::new(530,470),[System.Drawing.Point]::new(420,600),[System.Drawing.Point]::new(300,720),[System.Drawing.Point]::new(200,820))
)

$f3Red = @(
    [System.Drawing.Point[]]@([System.Drawing.Point]::new(1040,430),[System.Drawing.Point]::new(970,570),[System.Drawing.Point]::new(900,700),[System.Drawing.Point]::new(820,820)),
    [System.Drawing.Point[]]@([System.Drawing.Point]::new(610,430),[System.Drawing.Point]::new(500,570),[System.Drawing.Point]::new(340,700),[System.Drawing.Point]::new(190,820))
)
$f3Blue = @(
    [System.Drawing.Point[]]@([System.Drawing.Point]::new(960,480),[System.Drawing.Point]::new(1080,590),[System.Drawing.Point]::new(1210,700),[System.Drawing.Point]::new(1360,820)),
    [System.Drawing.Point[]]@([System.Drawing.Point]::new(530,470),[System.Drawing.Point]::new(590,580),[System.Drawing.Point]::new(650,700),[System.Drawing.Point]::new(700,820))
)

New-ContactOverlay -SourceName 'individual_F0_raw.png' -OutputName 'ref_f0_contact_overlay.png' -RedPair $f0Red -BluePair $f0Blue -Title 'F0 CONTACT: NEAR LEFT PAIR FORWARD'
New-ContactOverlay -SourceName 'individual_F3_raw.png' -OutputName 'ref_f3_contact_overlay.png' -RedPair $f3Red -BluePair $f3Blue -Title 'F3 CONTACT: FAR RIGHT PAIR FORWARD'
