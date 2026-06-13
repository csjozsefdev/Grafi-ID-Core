# Full Windows release build: embedded runtime + Tauri bundle.
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $RepoRoot

& (Join-Path $PSScriptRoot "create_icons.ps1")
& (Join-Path $PSScriptRoot "build_runtime.ps1")
& (Join-Path $PSScriptRoot "verify_packaged_runtime.ps1")

Set-Location (Join-Path $RepoRoot "desktop")
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "npm not found. Install Node.js to run tauri build."
}

if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) {
    throw "cargo not found. Install Rust (rustup) to run tauri build."
}

npm install
npm run tauri:build
if ($LASTEXITCODE -ne 0) {
    throw "tauri build failed with exit code $LASTEXITCODE"
}

$BundleRoot = Join-Path $RepoRoot "desktop\src-tauri\target\release\bundle"
$ReleaseExe = Join-Path $RepoRoot "desktop\src-tauri\target\release\graf-id-desktop.exe"
if (-not (Test-Path $ReleaseExe)) {
    throw "Missing release binary: $ReleaseExe"
}
if (-not (Test-Path $BundleRoot)) {
    throw "Missing bundle directory: $BundleRoot"
}

& (Join-Path $PSScriptRoot "verify_release_bundle.ps1")

Write-Host "Release build finished."
Write-Host "  Binary: $ReleaseExe"
Write-Host "  Bundle: $BundleRoot"
