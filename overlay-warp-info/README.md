# FDNY Collision Overlay

A live, click-through overlay for *FDNY Firefighter: American Hero* that shows
when the out-of-bounds warp is possible and what caused the last one.

## How the warp works

Genesis.dll keeps one shared "last collision hit" slot that every trace
overwrites. When the player's trace starts inside solid geometry, the engine
reports a hit without writing a new one, so the player is handed whatever is
still in the slot. If that plane isn't floor-like (normal.Y <= 0.9), the step
code moves the player there. That move is the warp.

## How the overlay works

- Attaches to `FDNYFirefighter.exe` with `pymem` and installs small code caves
  in Genesis.dll and the exe. The caves record every collision trace, every
  step commit and every simulated frame into a ring buffer.
- Reads the loaded map's `.bsp` from `<game>\Data\Maps` and replays the next
  frame's four sweeps (move, step-up, forward, step-down) to predict a warp.
- Draws three boxes: **WARP** (player state plus the next-frame prediction),
  **LAST WARP**, and **HISTORY** (the last 10 warp-capable hits).
- Puts the original game bytes back on exit.

## Usage

1. Download the newest `warp-info-build-*` release: `fdny_collision_overlay.zip`.
2. Copy `dgVoodoo.conf` over the game's `dgVoodoo.conf`. It sets fake
   fullscreen so the overlay can draw on top of the game.
3. Start the game, then run `fdny_collision_overlay.exe`.

Options: `--demo` (fake events, no game needed), `--windowed`,
`--corner tl|tr|bl|br`, `--maps DIR`.
Hotkeys: **F9** show/hide, **F10** freeze, **F12** clear history.

## Building

Every push to `main` that touches `overlay-warp-info/` triggers
`.github/workflows/release-overlay-warp-info.yml` (at the repo root). It builds
a one-file exe with PyInstaller on Windows and publishes a GitHub release
(`warp-info-build-<run number>`) with the exe, `dgVoodoo.conf` and a zip of both.

To build locally:

    python -m pip install pyinstaller pymem
    pyinstaller --onefile --windowed --name fdny_collision_overlay fdny_collision_overlay.py

Or run it from source: `python fdny_collision_overlay.py`.
