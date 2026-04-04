$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$exeName = "QuickImage"
$distDir = Join-Path $projectRoot "dist"
$buildDir = Join-Path $projectRoot "build"
$specFile = Join-Path $projectRoot "$exeName.spec"

if (Test-Path $distDir) {
    Remove-Item -LiteralPath $distDir -Recurse -Force
}

if (Test-Path $buildDir) {
    Remove-Item -LiteralPath $buildDir -Recurse -Force
}

if (Test-Path $specFile) {
    Remove-Item -LiteralPath $specFile -Force
}

python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name $exeName `
    --icon "icon.ico" `
    --add-data "i.png;." `
    "main.pyw"

Write-Host ""
Write-Host "Build completed: $distDir\$exeName.exe"
