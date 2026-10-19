# 📰 Newspaper Animation / Cutscene Trigger Analysis

## 🎯 Goal

Identify what triggers the newspaper animation at the end of a level, and find a memory address to monitor when it’s playing.

---

## 🔍 Key Findings

### 1. Video Playback Function

**Function:** `Video_PlayAVI`
**Address:** `0x00485650`
**Purpose:** Plays `.AVI` cutscenes using DirectShow interfaces.

**Comments:**

> Plays an AVI video file using DirectShow (`IGraphBuilder`, `IMediaControl`, `IVideoWindow`, `IBasicVideo`).
>
> **Key Memory Addresses for Monitoring:**
>
> * `0x005030c4` → `g_VideoPlayerActive`
>
>   * **Set to 1:** when a video/cutscene starts playing
>   * **Set to 0:** when video/cutscene finishes
>
> **Parameters:**
>
> * `hWnd`: Window handle for rendering video
> * `aviFilePath`: Path to the AVI file (e.g. `"Data\Movies\End.avi"`)
>
> The **newspaper animation** that plays after level completion uses this function.

---

### 2. Active Video Flag

**Variable:** `g_VideoPlayerActive`
**Address:** `0x005030c4`
**Type:** `uint8` or `bool`

**Behavior:**

* `1` → Video is currently playing (cutscene active)
* `0` → No video playing

**Usage:**

* Set in `Video_PlayAVI` (when playback starts)
* Cleared in `Video_ClearActiveFlag` (after playback ends)
* Referenced by other functions checking whether a cutscene is running

**✅ Memory address to monitor:**

```
0x005030c4
```

---

### 3. Related Global Variables

| Address      | Name                         | Purpose                            |
| ------------ | ---------------------------- | ---------------------------------- |
| `0x005030c4` | `g_VideoPlayerActive`        | Flag: video playing (1) or not (0) |
| `0x005030c8` | `g_VideoPlayer_GraphBuilder` | DirectShow graph builder pointer   |
| `0x005030cc` | `g_VideoPlayer_MediaControl` | DirectShow media control interface |
| `0x005030d0` | `g_VideoPlayer_VideoWindow`  | DirectShow video window interface  |
| `0x005030d4` | `g_VideoPlayer_BasicVideo`   | DirectShow basic video interface   |
| `0x005030d8` | `g_VideoPlayer_WindowHandle` | Handle to video playback window    |

---

### 4. Level Exit Trigger

**Function:** `LevelExit_OnPlayerTouch`
**Address:** `0x00460250`

**Description:**

> Called when the player touches the exit/goal at the end of a level.
> If the level is completed correctly, it triggers the **newspaper animation** by calling:
>
> ```c
> Video_PlayAVI("Data\\Movies\\End.avi");
> ```
>
> During this playback, `g_VideoPlayerActive` (`0x005030c4`) is set to **1**.

---

### 5. Supporting Functions

| Function Name                 | Address          | Description                                               |
| ----------------------------- | ---------------- | --------------------------------------------------------- |
| `Video_ClearActiveFlag`       | `0x004851c0`     | Sets `g_VideoPlayerActive` to 0 after playback finishes   |
| `Video_WaitForCompletion`     | `0x00485260`     | Waits until video playback is complete before returning   |
| `Level_ShowCompletionUI`      | `0x0048e370`     | Likely called after cutscene ends, to show results screen |
| `Video_PlayNewspaperCutscene` | *inferred alias* | Wrapper for playing `"Data\\Movies\\End.avi"`             |

---

## 🧩 Flow Summary

```
Player touches exit
        ↓
LevelExit_OnPlayerTouch()
        ↓
Video_PlayAVI("Data\\Movies\\End.avi")
        ↓
g_VideoPlayerActive = 1  ← monitor this address
        ↓
Video_WaitForCompletion()
        ↓
Video_ClearActiveFlag()
        ↓
g_VideoPlayerActive = 0
        ↓
Level_ShowCompletionUI()
```

---

## 🧠 Summary

* The **newspaper animation** (shown after a properly completed level) is played by `Video_PlayAVI` using `"Data\Movies\End.avi"`.
* The **memory flag** `0x005030c4` (`g_VideoPlayerActive`) is set to **1** during playback.
* Monitoring this address lets you detect when **any** video or cutscene — including the newspaper animation — is active.
* The flag is cleared (set to 0) after the cutscene finishes.

**✅ Recommended address to monitor:**

```
0x005030c4  →  g_VideoPlayerActive
```

---

## 📂 Video File Path Monitoring

### The Problem

* There is **no global memory address** that stores the current video filename.

### Why Not?

* Filepath is passed as a parameter on the stack.
* Converted to a wide-character string in a local stack buffer (~520 bytes).
* Passed directly to DirectShow's `RenderFile()`.
* Not stored globally; string exists only during the function call.

### What You CAN Monitor

**Option 1: Monitor String Literals (Read-Only Data)**

* Each video path is stored in `.rdata` section.
* Example:

  ```
  ```

0x004b5cd0 - "Data\Movies\End.avi" (newspaper video)

```
- Limitation: Cannot determine which video is currently active without hooking.

**Option 2: Hook / Breakpoint the Function**
- Set breakpoint on `Video_PlayAVI` (0x00485650).
- Examine stack:
```

ESP+8 → pointer to filename string

````
- Follow the pointer to read the actual filename.
- Cheat Engine example: Debugger → Set breakpoint → Examine [ESP+8].

**Option 3: Memory Scan During Playback**
- When `g_VideoPlayerActive == 1`, scan memory for `"Data\Movies\"`.
- Active video path may temporarily exist in memory (DirectShow buffers).
- Not reliable, depends on DirectShow implementation.

**DirectShow Interface Approach**
- `IGraphBuilder` pointer (`0x005030c8`) could be queried via COM methods for source filename.
- Complex, impractical for simple monitoring.

### Recommended Solution
- Use **code breakpoint/hook** approach.
- Cheat Engine Memory Record Example:
```xml
<CheatEntry>
<Description>"Video File Playing (Breakpoint Required)"</Description>
</CheatEntry>
````

---

## 🧰 Additional Context

* **Engine:** Genesis3D-based
* **Level Completion Logic:** Newspaper cutscene plays only when level completed correctly.
* **Cutscene Trigger:** Player touches exit/goal object.
* **Video System:** DirectShow with `IGraphBuilder`, `IMediaControl`, `IVideoWindow`, `IBasicVideo`.
