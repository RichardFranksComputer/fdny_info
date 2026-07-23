From the directory containing `overlay.py`:

`python overlay.py`

or

`python3 overlay.py`

if you have multiple installs

The overlay starts in the top-left of the screen; left-click-drag it
anywhere you like. Use the small `-`/`x` buttons in the top-right corner to
minimize or close it. It has a normal taskbar icon at all times, so you can
also minimize/restore/close it from there like any other app.

## Settings (overlay.ini)

All settings — including which memory values are shown (the label for each
one is free text purely for display; it has no effect on what's actually
read), the text color
(`text_color = R,G,B`, applies to everything except the status line), and
the font size (`font_size`, the window resizes to fit automatically) — live
in `overlay.ini`, next to `overlay.py` (or next to `FDNY_Overlay.exe` if
you're running the built exe). Double-click it to open it in Notepad, edit a
value, save, and restart the overlay. If the file is missing or a line can't
be understood, the overlay still starts with built-in defaults and shows a
warning instead of crashing.

Watch values are shown in two columns (label on the left, value on the
right, split down the middle) — labels that don't fit the column width are
truncated with "…", values are not.

## Building a standalone .exe

Requires Python + pip on PATH. From the `overlay` directory:

`.\build.ps1`

This installs PyInstaller if needed, runs the test suite (aborting the build
on any failure), and produces `dist\FDNY_Overlay.exe` (windowed, no console)
plus a copy of `overlay.ini` alongside it — the exe reads its settings from
`overlay.ini` in the same folder, so keep them together. If you need to see
startup/attach errors (e.g. "Process not found"), build a debug variant
instead:

`.\build.ps1 -Console`

A GitHub Actions workflow (`.github/workflows/build-overlay-exe.yml`) also builds
the exe on every push to `main` that touches `overlay/`, and can be run manually
from the Actions tab. The result (exe + overlay.ini) is uploaded as a workflow
artifact named `FDNY_Overlay` — no automatic Release is created.