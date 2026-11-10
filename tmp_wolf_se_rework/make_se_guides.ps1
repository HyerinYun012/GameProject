$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$root = $PSScriptRoot
$phases = @(
    [pscustomobject]@{ Red= 90; Blue=-90; RedLift= 0; BlueLift= 0; Label='right pair forward extreme / left pair backward extreme' },
    [pscustomobject]@{ Red= 35; Blue=-35; RedLift= 0; BlueLift=35; Label='right pair forward support / left pair backward swing' },
    [pscustomobject]@{ Red=-35; Blue= 35; RedLift= 0; BlueLift=55; Label='right pair rear support / left pair forward swing' },
    [pscustomobject]@{ Red=-90; Blue= 90; RedLift=20; BlueLift= 0; Label='right pair backward extreme / left pair forward extreme' },
    [pscustomobject]@{ Red=-35; Blue= 35; RedLift=35; BlueLift= 0; Label='right pair backward swing / left pair forward support' },
    [pscustomobject]@{ Red= 35; Blue=-35; RedLift=55; BlueLift= 0; Label='right pair forward swing / left pair rear support' }
)

function Add-Vector {
    param([System.Drawing.PointF]$Point, [double]$Amount, [double]$Lift)
    $unit = [Math]::Sqrt(0.5)
    return [System.Drawing.PointF]::new(
        [single]($Point.X + ($Amount * $unit)),
        [single]($Point.Y + ($Amount * $unit) - $Lift)
    )
}

for ($frame = 0; $frame -lt 6; $frame++) {
    $bitmap = [System.Drawing.Bitmap]::new(1024, 1024, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    try {
        $g = [System.Drawing.Graphics]::FromImage($bitmap)
        try {
            $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
            $g.Clear([System.Drawing.Color]::White)

            $bodyBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(218, 224, 224, 224))
            $outline = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(65, 65, 65), 10)
            $nearPen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(225, 25, 45), 32)
            $farPen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(25, 85, 220), 24)
            $nearBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(225, 25, 45))
            $farBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(25, 85, 220))
            $textBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::Black)
            $font = [System.Drawing.Font]::new('Arial', 25, [System.Drawing.FontStyle]::Bold)
            try {
                $state = $g.Save()
                $g.TranslateTransform(520, 400)
                $g.RotateTransform(28)
                $g.FillEllipse($bodyBrush, -300, -145, 600, 290)
                $g.DrawEllipse($outline, -300, -145, 600, 290)
                $g.Restore($state)

                $g.FillEllipse($bodyBrush, 705, 485, 220, 185)
                $g.DrawEllipse($outline, 705, 485, 220, 185)
                $g.DrawLine($outline, 300, 310, 145, 245)
                $g.DrawLine($outline, 816, 500, 800, 435)
                $g.DrawLine($outline, 860, 510, 875, 455)

                $nearHindJoint = [System.Drawing.PointF]::new(360, 500)
                $nearForeJoint = [System.Drawing.PointF]::new(650, 630)
                $farHindJoint = [System.Drawing.PointF]::new(410, 380)
                $farForeJoint = [System.Drawing.PointF]::new(690, 520)
                $nearHindBase = [System.Drawing.PointF]::new(330, 720)
                $nearForeBase = [System.Drawing.PointF]::new(630, 845)
                $farHindBase = [System.Drawing.PointF]::new(410, 620)
                $farForeBase = [System.Drawing.PointF]::new(705, 725)

                $nearHindPaw = Add-Vector $nearHindBase $phases[$frame].Red $phases[$frame].RedLift
                $nearForePaw = Add-Vector $nearForeBase $phases[$frame].Red $phases[$frame].RedLift
                $farHindPaw = Add-Vector $farHindBase $phases[$frame].Blue $phases[$frame].BlueLift
                $farForePaw = Add-Vector $farForeBase $phases[$frame].Blue $phases[$frame].BlueLift

                $g.DrawLine($farPen, $farHindJoint, $farHindPaw)
                $g.DrawLine($farPen, $farForeJoint, $farForePaw)
                $g.FillEllipse($farBrush, $farHindPaw.X - 24, $farHindPaw.Y - 18, 48, 36)
                $g.FillEllipse($farBrush, $farForePaw.X - 24, $farForePaw.Y - 18, 48, 36)
                $g.DrawLine($nearPen, $nearHindJoint, $nearHindPaw)
                $g.DrawLine($nearPen, $nearForeJoint, $nearForePaw)
                $g.FillEllipse($nearBrush, $nearHindPaw.X - 30, $nearHindPaw.Y - 22, 60, 44)
                $g.FillEllipse($nearBrush, $nearForePaw.X - 30, $nearForePaw.Y - 22, 60, 44)

                $title = 'SE pace f{0}: RED=wolf right/near fore+hind; BLUE=wolf left/far fore+hind' -f $frame
                $g.DrawString($title, $font, $textBrush, 28, 25)
                $g.DrawString($phases[$frame].Label, $font, $textBrush, 28, 62)
            }
            finally {
                $bodyBrush.Dispose(); $outline.Dispose(); $nearPen.Dispose(); $farPen.Dispose()
                $nearBrush.Dispose(); $farBrush.Dispose(); $textBrush.Dispose(); $font.Dispose()
            }
        }
        finally { $g.Dispose() }
        $bitmap.Save((Join-Path $root ('guide_SE_{0}.png' -f $frame)), [System.Drawing.Imaging.ImageFormat]::Png)
    }
    finally { $bitmap.Dispose() }
}
