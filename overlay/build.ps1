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

# Runs a native command (python/pyinstaller, not a PowerShell cmdlet) with
# $ErrorActionPreference relaxed just for that call. In PowerShell 5.1, any
# stderr output from a native command - even a normal warning/notice, not
# just a real failure - gets wrapped into a terminating NativeCommandError
# under "Stop", which would abort the whole build on things like pip's own
# notices or unittest's verbose (stderr-by-default) test output. Exit code
# is checked explicitly afterward instead, so real failures still abort.
function Invoke-Native {
    param([string]$Description, [scriptblock]$Command)
    $prevEAP = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & $Command
    $exitCode = $LASTEXITCODE
    $ErrorActionPreference = $prevEAP
    if ($exitCode -ne 0) {
        throw "$Description failed (exit code $exitCode)"
    }
}

$ScriptDir     = Split-Path -Parent $MyInvocation.MyCommand.Path
$SourceFile    = Join-Path $ScriptDir "overlay.py"
$EngineFile    = Join-Path $ScriptDir "watch_engine.py"
$ProcReaderFile = Join-Path $ScriptDir "process_reader.py"
$ConfigFile    = Join-Path $ScriptDir "overlay.ini"
$IconFile      = Join-Path $ScriptDir "icon.ico"
$AppName       = "FDNY_Overlay"

if (-not (Test-Path $SourceFile)) {
    throw "Could not find overlay.py at $SourceFile"
}
if (-not (Test-Path $EngineFile)) {
    throw "Could not find watch_engine.py at $EngineFile"
}
if (-not (Test-Path $ProcReaderFile)) {
    throw "Could not find process_reader.py at $ProcReaderFile"
}
if (-not (Test-Path $ConfigFile)) {
    throw "Could not find overlay.ini at $ConfigFile"
}
if (-not (Test-Path $IconFile)) {
    throw "Could not find icon.ico at $IconFile"
}

$ValuesGameFiles = Get-ChildItem -Path $ScriptDir -Filter "values-*.py"
if (-not $ValuesGameFiles) {
    throw "Could not find any values-*.py file (e.g. values-fdny.py) in $ScriptDir"
}

# Ensure PyInstaller is installed. A non-zero exit here just means "not
# installed yet", not a real failure - don't use Invoke-Native (which
# throws on non-zero), just relax $ErrorActionPreference for this one check.
$prevEAP = $ErrorActionPreference
$ErrorActionPreference = "Continue"
python -c "import PyInstaller" 2>$null
$pyInstallerMissing = ($LASTEXITCODE -ne 0)
$ErrorActionPreference = $prevEAP
if ($pyInstallerMissing) {
    Write-Host "PyInstaller not found, installing..."
    Invoke-Native "PyInstaller install" { python -m pip install --upgrade pyinstaller }
}

Write-Host "Running tests..."
Invoke-Native "Tests" { python -m unittest discover -s "$ScriptDir\tests" -v }

$WindowModeArg = if ($Console) { "--console" } else { "--noconsole" }

Push-Location $ScriptDir
try {
    # overlay.py's own imports (`from watch_engine import ...`, `from
    # process_reader import ...`) are enough for PyInstaller to discover and
    # bundle both modules automatically via static analysis - no --hidden-import or
    # --add-data needed for them, only for overlay.ini/icon.ico below, which
    # are read from disk at runtime rather than imported.
    Invoke-Native "PyInstaller build" {
        python -m PyInstaller `
            --onefile `
            $WindowModeArg `
            --name $AppName `
            --icon $IconFile `
            --distpath "$ScriptDir\dist" `
            --workpath "$ScriptDir\build" `
            --specpath "$ScriptDir" `
            $SourceFile
    }

    # overlay.ini, icon.ico, and values-*.py are read from next to the exe at
    # runtime (not bundled inside the onefile package), so they must ship
    # alongside it, not just in the repo. --icon above only sets the .exe
    # file's own icon in Explorer; ICON_PATH in overlay.py is what sets the
    # running window's taskbar/Alt-Tab icon, and needs the file on disk at
    # runtime too. values-*.py is loaded dynamically by path (not a normal
    # import), so PyInstaller's static analysis can't discover it on its
    # own - it needs the same explicit copy as the other two.
    Copy-Item -Path $ConfigFile -Destination "$ScriptDir\dist\overlay.ini" -Force
    Copy-Item -Path $IconFile -Destination "$ScriptDir\dist\icon.ico" -Force
    foreach ($f in $ValuesGameFiles) {
        Copy-Item -Path $f.FullName -Destination "$ScriptDir\dist\$($f.Name)" -Force
    }

    Write-Host "`nBuild complete: $ScriptDir\dist\$AppName.exe (+ overlay.ini, icon.ico, $($ValuesGameFiles.Name -join ', '))"
}
finally {
    Pop-Location
}
