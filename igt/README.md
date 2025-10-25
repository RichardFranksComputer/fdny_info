# Timer System Analysis Summary

UNVERIFIED - output from ghidrAssist, could be hallucinated, do not trust this info

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