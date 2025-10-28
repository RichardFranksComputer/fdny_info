# Newspaper Animation Trigger Analysis

## Objective
Determine what triggers the newspaper animation (cutscene) to play at the end of a level and identify a memory address that indicates when it is active.

---

## Summary of Findings

**Key discovery**
- The newspaper animation is played via:
  ```
  Video_PlayAVI("Data\Movies\End.avi")
  ```
- The memory flag to monitor is:
  ```
  0x005030C4 → g_VideoPlayerActive
  ```
  - `1` = video is playing  
  - `0` = no video is playing

Monitoring `0x005030C4` should let you detect when the newspaper cutscene (or any video) is active.

---

## Relevant Functions

| Function Name               | Description |
|-----------------------------|-------------|
| `Video_PlayAVI`             | Plays an AVI using DirectShow interfaces (`IGraphBuilder`, `IMediaControl`, `IVideoWindow`, `IBasicVideo`). Sets `g_VideoPlayerActive` (0x005030C4) to `1` on start. |
| `Video_ClearActiveFlag`     | Clears `g_VideoPlayerActive` (sets to `0`) when playback finishes. |
| `Video_WaitForCompletion`   | Waits for playback to finish (blocks or polls until video end). |
| `LevelExit_OnPlayerTouch`   | Called when the player reaches a level exit; calls `Video_PlayAVI("Data\Movies\End.avi")`. |
| `Level_EndHandler`          | Level completion logic that may interact with the sequence above. |

---

## Key Memory Addresses

| Address     | Symbol                        | Description |
|-------------|-------------------------------|-------------|
| `0x005030C4`| `g_VideoPlayerActive`         | Byte flag set to `1` while any video is playing; `0` otherwise. Primary address to monitor. |
| `0x005030C8`| `g_VideoPlayer_GraphBuilder`  | `IGraphBuilder` pointer (DirectShow). |
| `0x005030CC`| `g_VideoPlayer_MediaControl`  | `IMediaControl` pointer (DirectShow). |
| `0x005030D0`| `g_VideoPlayer_VideoWindow`   | `IVideoWindow` pointer (DirectShow). |
| `0x005030D4`| `g_VideoPlayer_BasicVideo`    | `IBasicVideo` pointer (DirectShow). |
| `0x005030D8`| `g_VideoPlayer_WindowHandle`  | Window handle used for rendering video playback. |

---

## Control Flow (high-level)

1. **Player touches exit**  
   `LevelExit_OnPlayerTouch` runs → verifies completion → calls `Video_PlayAVI("Data\Movies\End.avi")`.

2. **Video_PlayAVI**  
   - sets `g_VideoPlayerActive = 1`  
   - initializes DirectShow interfaces  
   - starts playback  
   - waits for completion (`Video_WaitForCompletion`)  
   - calls `Video_ClearActiveFlag` → sets `g_VideoPlayerActive = 0`

---

## Recommendations for Monitoring

- Use a memory watcher (Cheat Engine, custom injector, or a small script) to **watch byte** at `0x005030C4`.
- Optionally set a **write breakpoint** on `0x005030C4` to catch the instant it becomes `1`.
- If the video is very brief or you suspect a single-tick transition, prefer a breakpoint or OS-level memory-write hook over polling.

---

## Notes & Caveats

- The cutscene itself is not a unique “newspaper” function — it's just an AVI file played via the generic video system.
- If monitoring `0x005030C4` appears to “not work”:
  - Confirm the game executable and addresses match (ASLR / different build can shift addresses).
  - Confirm you have the correct process attached and permission to read/monitor memory.
  - Consider that the flag may be toggled very quickly — use a write breakpoint.

---

## Minimal Cheatsheet

- **Detect cutscene start/stop:** watch `0x005030C4` (`g_VideoPlayerActive`)  
- **Cutscene file:** `Data\Movies\End.avi`  
- **Trigger location:** `LevelExit_OnPlayerTouch` → calls `Video_PlayAVI`

---

## TL;DR
Monitor `0x005030C4` (`g_VideoPlayerActive`) — it is set to `1` while the newspaper (End.avi) plays.  
If that address doesn’t toggle, the likely causes are:
- Address mismatch (different build / ASLR)
- Insufficient permissions
- Flag toggled too briefly (use a write breakpoint)
