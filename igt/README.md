# Timer System Analysis Summary

## Overview

The game uses a real-world timing system based on Windows `timeGetTime()` API, making it highly reliable for speedrun timing. The timer is **NOT** frame-dependent and provides accurate real-world time measurement.

---

## Key Functions

### 1. Timer_Update (`0x0042bf70`)

**Purpose:** Core timer update logic that calculates elapsed time

**Timing Source:** `timeGetTime()` - Windows multimedia timer (1ms precision)

**Key Features:**
- Calculates delta time between frames
- Applies game speed multiplier from global variable `0x55ea74`
- Implements frame limiting (sleeps if delta < 0.1s)
- Updates minutes, seconds, and centiseconds (hundredths of seconds)
- Respects pause state

### 2. DualTimer_Update (`0x0042c080`)

**Purpose:** Manages two independent timers (normal + alternate)

**Behavior:**
- Switches between Timer 1 and Timer 2 based on flags
- Copies active timer values to display variables
- Called from `Game_UpdateTick` every frame

### 3. Timer_Pause (`0x0042bf20`)

**Purpose:** Pauses timer by setting pause flag and recording pause start time

**Safe for speedruns:** Properly accounts for paused time

### 4. Timer_Resume (`0x0042bf50`)

**Purpose:** Resumes timer and adds pause duration to offset

**Maintains accuracy:** Pause time doesn't count toward elapsed time

### 5. DualTimer_Init (`0x0042c1a0`)

**Purpose:** Initializes both timers to 0, sets them as paused

**Called at:** Level/game start

---

## Critical Memory Addresses for Hooking

### Global Timer State

| Address | Name | Description | Size |
|---------|------|-------------|------|
| `0x00502ab8` | `g_DualTimer` | Primary timer structure | 32 bytes |
| `0x00502ad8` | `g_DualTimer_Alt` | Alternate timer structure | 32 bytes |
| `0x00502af8` | `g_TimerSelectFlag` | Which timer is active (0 or 1) | 4 bytes |

### Timer Structure Offsets (32 bytes per timer)
```
+0x00: lastUpdateTimeMs    - Last timeGetTime() value (DWORD)
+0x04: currentTimeMs       - Current accumulated time in ms (DWORD)
+0x08: pauseOffsetMs       - Time offset when paused (DWORD)
+0x0C: pauseStartTimeMs    - When pause started (DWORD)
+0x10: minutes             - Displayed minutes (int)
+0x14: seconds             - Displayed seconds (int)
+0x18: centiseconds        - Displayed centiseconds/hundredths (int)
+0x1C: isPaused            - Pause flag (bool/byte)
```

### Display Values (Updated by DualTimer_Update)

| Address | Offset from g_DualTimer | Description |
|---------|-------------------------|-------------|
| `g_DualTimer + 0x44` | `+0x44` | Current minutes |
| `g_DualTimer + 0x48` | `+0x48` | Current seconds |
| `g_DualTimer + 0x4C` | `+0x4C` | Current centiseconds |

### Game Speed Multiplier

| Address | Description |
|---------|-------------|
| `0x0055ea74` | Game speed scalar (float) - affects timer rate |

---

## Recommended Hook Points for LiveSplit

### For Real-Time Timing

**Option 1: Hook Timer_Update (`0x0042bf70`)**
- Read from: `timerState + 0x04` (`currentTimeMs`)
- This gives raw accumulated milliseconds
- **Most reliable option**

**Option 2: Hook DualTimer_Update (`0x0042c080`)**
- Read display values after this function executes
  - Minutes: `*(int*)(g_DualTimer + 0x44)`
  - Seconds: `*(int*)(g_DualTimer + 0x48)`
  - Centiseconds: `*(int*)(g_DualTimer + 0x4C)`

### For Pause Detection

- **Check:** `*(byte*)(g_DualTimer + 0x1C)` for pause state
- When `isPaused == true`, timer is paused

### For Timer Start/Stop Events

- **Timer Start:** Hook `Timer_Resume` (`0x0042bf50`)
- **Timer Stop:** Hook `Timer_Pause` (`0x0042bf20`)
- **Timer Init:** Hook `DualTimer_Init` (`0x0042c1a0`) for run start

---

## Reliability Assessment

### ✅ HIGHLY RELIABLE for Speedrun Timing

**Reasons:**
- **Uses timeGetTime():** Real-world clock, not frame-dependent
- **1ms precision:** Windows multimedia timer standard
- **Pause accounting:** Properly handles paused time
- **Independent of FPS:** Timer runs regardless of frame rate
- **Sleep protection:** Caps delta time to prevent huge jumps

### ⚠️ Potential Variables to Watch

**Game Speed Multiplier (`0x55ea74`):**
- If modified (cheats/mods), timer runs faster/slower
- Default should be `1.0f`
- Check this value for legitimacy

**Dual Timer System:**
- Game switches between two timers
- Verify which timer (`g_TimerSelectFlag`) is being used
- Both timers use same `timeGetTime()` source

**Pause State:**
- Ensure LiveSplit respects the `isPaused` flag
- Paused time should NOT count

---

## Recommended LiveSplit Integration
```csharp
// Pseudo-code for LiveSplit auto-splitter
uint baseAddr = 0x00502ab8; // g_DualTimer

// Read timer values
int minutes = ReadInt(baseAddr + 0x44);
int seconds = ReadInt(baseAddr + 0x48);
int centiseconds = ReadInt(baseAddr + 0x4C);
bool isPaused = ReadByte(baseAddr + 0x1C);

// Calculate total time
float totalSeconds = (minutes * 60) + seconds + (centiseconds / 100.0f);

// Check game speed (anti-cheat)
float gameSpeed = ReadFloat(0x0055ea74);
if (gameSpeed != 1.0f) {
    // Flag as modified timing
}
```

---

## Conclusion

This timer system is **excellent for speedrun timing**. It uses real-world time via `timeGetTime()`, properly handles pauses, and is independent of frame rate. The memory addresses are stable and easy to hook. Your LiveSplit auto-splitter should be very reliable when hooking these addresses.