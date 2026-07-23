<#
Packages overlay.py into a single-file Windows executable (dist\FDNY_Overlay.exe)
using PyInstaller. Run from anywhere; paths resolve relative to this script.

By default the exe is windowed (no console), matching normal overlay use.
Pass -Console to keep the console window, which shows startup/attach errors
like "Process not found" — useful when troubleshooting.
#>

param(
    [switch]$Console
)

$ErrorActionPreference = "Stop"

$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$SourceFile = Join-Path $ScriptDir "overlay.py"
$ConfigFile = Join-Path $ScriptDir "overlay.ini"
$AppName    = "FDNY_Overlay"

if (-not (Test-Path $SourceFile)) {
    throw "Could not find overlay.py at $SourceFile"
}
if (-not (Test-Path $ConfigFile)) {
    throw "Could not find overlay.ini at $ConfigFile"
}

# Ensure PyInstaller is installed
python -c "import PyInstaller" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller not found, installing..."
    python -m pip install --upgrade pyinstaller
}

Write-Host "Running tests..."
python -m unittest discover -s "$ScriptDir\tests" -v
if ($LASTEXITCODE -ne 0) {
    throw "Tests failed - aborting build."
}

$WindowModeArg = if ($Console) { "--console" } else { "--noconsole" }

Push-Location $ScriptDir
try {
    python -m PyInstaller `
        --onefile `
        $WindowModeArg `
        --name $AppName `
        --distpath "$ScriptDir\dist" `
        --workpath "$ScriptDir\build" `
        --specpath "$ScriptDir" `
        $SourceFile

    # overlay.ini is read from next to the exe at runtime (not bundled inside
    # the onefile package), so it must ship alongside it, not just in the repo.
    Copy-Item -Path $ConfigFile -Destination "$ScriptDir\dist\overlay.ini" -Force

    Write-Host "`nBuild complete: $ScriptDir\dist\$AppName.exe (+ overlay.ini)"
}
finally {
    Pop-Location
}
