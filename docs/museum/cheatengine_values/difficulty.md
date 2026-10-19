# The Epic Saga of Finding a Single Memory Address for LiveSplit

Or: How We Spent Hours Reversing FMOD Sound Playback in a 20+ Year Old Game

## The Goal

Monitor when a specific sound plays in FDNY Firefighter (a Genesis3D game from ~2004) so LiveSplit can auto-split a speedrun. Sounds simple, right? WRONG.

## Step 1: The Initial Setup (Seemed Easy)

1. Set breakpoint on `FMOD.FSOUND_PlaySoundEx` in the `FMOD.dll`
2. Added condition: `ECX == 0x0a902f00` (the sound buffer we wanted to track)
3. Breakpoint hit! Found 4 instruction addresses that access this value:
   - `0x004c6d64`
   - `0x004a0ce3`
   - `0x004a010b`
   - `0x004a014c`

**Problem:** These are just instructions that READ the sound buffer pointer. We need to find where the channel handle (the thing that tells us if sound is playing) gets STORED.

## Step 2: Reverse Engineering the Game Code (First Layer of Hell)

Used an MCP Ghidra agent to analyze those 4 addresses:

### Address 1: `0x004c6d64`

- **Result:** FALSE POSITIVE
- It was just `___ascii_stricmp` (string comparison function)
- The `0x0a902f00` value happened to be in a string being compared
- **Wasted time:** 15 minutes

### Address 2: `0x004a0ce3` ✅ THE GOLDEN ONE

- Inside `SoundSystem_PlaySound` function
- Calls a wrapper `FMOD_PlaySound` at `0x004a0cf9`
- **CRITICAL INSTRUCTION FOUND:** `0x004a0d04: MOV dword ptr [ESI], EAX`
  - This stores the channel handle!
  - `EAX` = channel handle returned from FMOD
  - `ESI` = SoundChannel object pointer

### Addresses 3 & 4: `0x004a010b` and `0x004a014c`

- Both in the same function `FMOD_PlaySound` (low-level wrapper)
- Just helper functions that return channel via output parameter
- Led back to address 2

**Time spent:** 2 hours of agent analysis, function tracing, and decompilation

## Step 3: Runtime Debugging (Second Layer of Hell)

Set breakpoint at `0x004a0d04` (where channel gets stored) and ran the game:

### First attempt:

- Hit breakpoint 5 times in quick succession
- ESI values all over the place (heap addresses):
  - `0x0A998328`
  - `0x0A942298`
  - `0x0A99F978`
  - `0x0A988AF8`
  - `0x0A90F728`

**Problem:** Which one is OUR sound?!

## Step 4: Isolating the Target Sound (The Confusion)

Set TWO breakpoints:

1. Memory access on `0x0a902f00`
2. Instruction at `0x004a0d04`

Execution flow:
