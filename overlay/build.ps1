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
$AppName    = "FDNY_Overlay"

if (-not (Test-Path $SourceFile)) {
    throw "Could not find overlay.py at $SourceFile"
}

# Ensure PyInstaller is installed
python -c "import PyInstaller" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller not found, installing..."
    python -m pip install --upgrade pyinstaller
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

    Write-Host "`nBuild complete: $ScriptDir\dist\$AppName.exe"
}
finally {
    Pop-Location
}
