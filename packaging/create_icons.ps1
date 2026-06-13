# Minimal Graf-Id app icons for Tauri bundle (Windows).
$ErrorActionPreference = "Stop"
$IconDir = Join-Path $PSScriptRoot "..\desktop\src-tauri\icons"
New-Item -ItemType Directory -Force -Path $IconDir | Out-Null

Add-Type -AssemblyName System.Drawing

function New-GrafIcon($size, $path) {
    $bmp = New-Object System.Drawing.Bitmap $size, $size
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.Clear([System.Drawing.Color]::FromArgb(26, 29, 35))
    $brush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(138, 180, 248))
    $fontSize = [float]($size * 0.38)
    $font = New-Object System.Drawing.Font("Segoe UI", $fontSize, [System.Drawing.FontStyle]::Bold)
    $format = New-Object System.Drawing.StringFormat
    $format.Alignment = [System.Drawing.StringAlignment]::Center
    $format.LineAlignment = [System.Drawing.StringAlignment]::Center
    $rect = New-Object System.Drawing.RectangleF 0, 0, $size, $size
    $g.DrawString("G", $font, $brush, $rect, $format)
    $g.Dispose()
    $bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
    $bmp.Dispose()
}

New-GrafIcon 32 (Join-Path $IconDir "32x32.png")
New-GrafIcon 128 (Join-Path $IconDir "128x128.png")
New-GrafIcon 256 (Join-Path $IconDir "128x128@2x.png")
Write-Host "Icons written to $IconDir"
Write-Host "Run from desktop/: npx tauri icon src-tauri/icons/128x128.png  (generates icon.ico for MSI/NSIS)"
