# Changelog

One line per change to `overlay/`, newest first.

- 2026-07-22: Added square minimize/close buttons (`-`/`x`, 50%-blended-green border), a `text_color` setting in `overlay.ini` driving all non-status text, and a test-run step in `build.ps1`/CI that aborts the build on failure; added `tests/test_colors.py`; added CLAUDE.md guidance to keep source comments short.
- 2026-07-22: Moved all settings, including `WATCHES`, out of `overlay.py` into `overlay.ini` (stdlib `configparser`, human-readable, opens in Notepad by default) so the built exe can be reconfigured without a rebuild; `build.ps1`/CI now ship `overlay.ini` alongside `FDNY_Overlay.exe`. Added `tests/test_config.py`.
- 2026-07-22: Added `CLAUDE.md` (feature list + testing/README/changelog guidance for agents) and this changelog.
- 2026-07-22: Added `ProcessConnection` state machine so the overlay launches without the game running, auto-attaches, retries `OpenProcess` up to 5x, detects the game exiting, and re-attaches if it's relaunched — status shown in-overlay instead of printed to console. Added unit tests in `tests/test_process_connection.py`.
- 2026-07-22: Added a right-click context menu (`tk.Menu` with "Close") as a possible way to close the overlay without Task Manager; later reverted to unwired/inactive.
- 2026-07-22: Added `build.ps1` and `.github/workflows/build-overlay-exe.yml` to package `overlay.py` into a standalone `dist/FDNY_Overlay.exe` via PyInstaller, uploaded as a workflow artifact.
- 2026-07-22: Added configurable corner-anchoring to the game window (`ANCHOR_CORNER`, `ANCHOR_MARGIN_X/Y`, `ANCHOR_REFRESH_MS`), replacing the fixed `+40+40` startup position; drag offset now persists across re-anchoring.
