# Build embedded Python runtime for Graf-Id desktop (Windows).
# Output: desktop/src-tauri/runtime/ (bundled by Tauri as resources)
# Requires: repo .venv with graf-id installed (pip install -e ".[dev]")

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$OutputDir = Join-Path $RepoRoot "desktop\src-tauri\runtime"
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    throw "Missing .venv. From repo root run: python -m venv .venv; .venv\Scripts\pip install -e `".[dev]`""
}

function Normalize-WindowsPath {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) {
        return $null
    }
    $normalized = $Path.Trim()
    if ($normalized.StartsWith("\\?\")) {
        $normalized = $normalized.Substring(4)
    }
    return $normalized
}

function Assert-RuntimePath {
    param(
        [string]$Path,
        [string]$Label
    )
    $normalized = Normalize-WindowsPath $Path
    if ([string]::IsNullOrWhiteSpace($normalized)) {
        throw "$Label is missing. Expected a Python install directory from packaging\_python_base_info.py."
    }
    if (-not (Test-Path $normalized)) {
        throw "$Label was not found: $normalized"
    }
    return $normalized
}

Write-Host "Building Graf-Id embedded runtime -> $OutputDir"

$pyInfoScript = Join-Path $PSScriptRoot "_python_base_info.py"
if (-not (Test-Path $pyInfoScript)) {
    throw "Missing helper script: $pyInfoScript"
}

$pyMeta = & $VenvPython $pyInfoScript
if ($LASTEXITCODE -ne 0) {
    throw "Failed to resolve base Python install via $pyInfoScript"
}
if ([string]::IsNullOrWhiteSpace($pyMeta)) {
    throw "No output from $pyInfoScript. Expected JSON with base Python path."
}

$meta = $pyMeta | ConvertFrom-Json
$Base = Assert-RuntimePath -Path $meta.base -Label "Base Python install"
$Ver = [string]$meta.ver
if ([string]::IsNullOrWhiteSpace($Ver)) {
    throw "Python version tag is missing from $pyInfoScript output."
}

$BasePythonExe = Join-Path $Base "python.exe"
if (-not (Test-Path $BasePythonExe)) {
    throw "Base Python executable was not found: $BasePythonExe"
}

Write-Host "Using base Python install: $Base"

if (Test-Path $OutputDir) {
    Remove-Item -Recurse -Force $OutputDir
}
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

function Copy-IfExists($src, $destDir) {
    if (Test-Path $src) {
        Copy-Item -Path $src -Destination $destDir -Force
        return $true
    }
    return $false
}

# Core interpreter files from the base Python install
$binaryNames = @(
    "python.exe",
    "python$Ver.dll",
    "python3.dll",
    "vcruntime140.dll",
    "vcruntime140_1.dll"
)
foreach ($name in $binaryNames) {
    if (-not (Copy-IfExists (Join-Path $Base $name) $OutputDir)) {
        Copy-IfExists (Join-Path $Base "Scripts\$name") $OutputDir | Out-Null
    }
}

$dlls = Join-Path $Base "DLLs"
if (Test-Path $dlls) {
    Copy-Item -Path $dlls -Destination (Join-Path $OutputDir "DLLs") -Recurse -Force
}

# Standard library (required for encodings and stdlib imports)
$baseLib = Join-Path $Base "Lib"
$outLib = Join-Path $OutputDir "Lib"
if (Test-Path $baseLib) {
    Copy-Item -Path $baseLib -Destination $outLib -Recurse -Force
}
New-Item -ItemType Directory -Force -Path "$outLib\site-packages" | Out-Null

# Do not ship python._pth — it enables embed isolation and breaks a portable Lib/ layout.
Get-ChildItem -Path $OutputDir -Filter "python$Ver._pth" -ErrorAction SilentlyContinue | Remove-Item -Force

Write-Host "Installing graf-id and dependencies into runtime..."
$SitePackages = Join-Path $OutputDir "Lib\site-packages"
& $VenvPython -m pip install --upgrade pip -q
& $VenvPython -m pip install typer --target $SitePackages -q
if (Test-Path "$SitePackages\grafid") {
    Remove-Item -Recurse -Force "$SitePackages\grafid"
}
Copy-Item -Path (Join-Path $RepoRoot "grafid") -Destination "$SitePackages\grafid" -Recurse -Force

$RuntimePython = Join-Path $OutputDir "python.exe"
if (-not (Test-Path $RuntimePython)) {
    throw "runtime/python.exe was not created"
}

Write-Host "Verifying embedded imports..."
$prevPP = $env:PYTHONPATH
$env:PYTHONPATH = $SitePackages
$env:PYTHONNOUSERSITE = "1"
Push-Location $OutputDir
try {
    & $RuntimePython -c "import encodings; import grafid; import typer; print('ok', grafid.__file__)"
    if ($LASTEXITCODE -ne 0) {
        throw "Embedded runtime verification failed"
    }
} finally {
    Pop-Location
    $env:PYTHONPATH = $prevPP
    Remove-Item Env:PYTHONNOUSERSITE -ErrorAction SilentlyContinue
}

Write-Host "Runtime build complete."
