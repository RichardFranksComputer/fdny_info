From the directory containing `overlay.py`:

`python overlay.py`

or

`python3 overlay.py`

if you have multiple installs

## Building a standalone .exe

Requires Python + pip on PATH. From the `overlay` directory:

`.\build.ps1`

This installs PyInstaller if needed and produces `dist\FDNY_Overlay.exe` (windowed,
no console). If you need to see startup/attach errors (e.g. "Process not found"),
build a debug variant instead:

`.\build.ps1 -Console`

A GitHub Actions workflow (`.github/workflows/build-overlay-exe.yml`) also builds
the exe on every push to `main` that touches `overlay/`, and can be run manually
from the Actions tab. The result is uploaded as a workflow artifact named
`FDNY_Overlay` — no automatic Release is created.