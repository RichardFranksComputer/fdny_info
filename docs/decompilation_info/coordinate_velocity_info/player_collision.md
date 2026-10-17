# FDNY Firefighter – Player Collision Hull Reverse Engineering (README)

## Overview

This README summarizes the full investigation into **where the player collision hull (height / extents / bounds)** actually lives in memory for *FDNY Firefighter*, and how to correctly monitor it using Cheat Engine.

The key outcome is that **player collision bounds are NOT stored persistently in the Genesis actor structure**. Instead, they are **computed dynamically by fdny.exe** and passed into Genesis.dll collision functions every movement frame.

---

## Initial Assumptions (Some Proven False)

- Player collision hull was assumed to be stored in a persistent actor structure:
  - `PlayerCollisionActor = [[fdny.exe + PlayerObject] + 0x3460]`
  - Extents assumed at offsets `0x18–0x2C` (MinX, MinY, MinZ, MaxX, MaxY, MaxZ)
- Genesis.dll functions like `geActor_SetExtBox` were assumed to define collision bounds
- These fields appeared static and never changed during movement

**Result:**  
These actor ExtBox values are **rendering / culling bounds only** and do **not** represent player movement collision.

---

## Cheat Engine Pointer Confusion (Resolved)

### Problem
- Adding offsets like `0x1C` as pointers caused nonsense values (e.g. `6.24e-39`)
- CE pointer chains were incorrectly extended into non-pointer fields
- Some offsets resolved to values like `0x0043F660`, which *looked* like addresses

### Resolution
- `0x18–0x2C` are **floats**, not pointers
- Seeing address-like values here indicated **misinterpretation of data**, not real pointers
- Even when set up correctly, these actor fields never changed → confirmed irrelevant

---

## Genesis.dll Investigation Results

### geActor_SetExtBox / geActor_GetExtBox
- Writes to offsets `0x18–0x2C`
- Only used for rendering/static bounds
- Not called during jump, crouch, stand, or movement

### Key Insight
Genesis.dll **does not own** the player collision hull. It only *uses* bounds passed in by fdny.exe.

---

## Attempted Genesis.dll Global Monitoring (Limited Use)

Certain Genesis.dll global addresses temporarily store collision extents during collision tests:

```
Genesis.dll+0x362E78  MinX
Genesis.dll+0x362E7C  MinY (bottom)
Genesis.dll+0x362E80  MinZ
Genesis.dll+0x362F00  MaxX
Genesis.dll+0x362F04  MaxY (top)
Genesis.dll+0x362F08  MaxZ
```

These are written inside:
- `geWorld_TestModelMove`
- `geWorld_Collision`

**Important:**  
These globals are:
- Transient scratch storage
- Only valid during the collision call
- Often zero or overwritten outside that window

Useful for **breakpoints**, but not ideal for continuous monitoring.

---

## FINAL DISCOVERY (Correct Location)

### The Real Collision Hull Location

The **actual working collision hull values** were found at offsets like:

```
+0xEE4
+0xEE8
+0xEEC
```

These:
- Are floats
- Change correctly during jump / crouch / movement
- Represent MinY / MaxY / height (or related Y extents)
- Exist in **fdny.exe-owned memory**, not Genesis.dll

### What These Offsets Are

These offsets belong to:
- A **player movement / collision state struct**, or
- A **stack frame** used just before calling Genesis collision functions

fdny.exe computes the collision hull like:

```c
Vec3 MinExtents;
Vec3 MaxExtents;

ComputePlayerCollisionHull(&MinExtents, &MaxExtents, playerState);

geWorld_TestModelMove(..., &MinExtents, &MaxExtents, ...);
```

The values at `EE4 / EE8 / EEC` are **that Min/Max data before it ever reaches Genesis.dll**.

---

## Why Previous Approaches Failed

| Attempt | Why It Failed |
|------|--------------|
Actor ExtBox | Static render bounds only |
Genesis globals | Too transient |
Pointer chains | Hull not stored persistently |
Watching geActor_SetExtBox | Not used for movement |

---

## What Actually Matters

✔ Collision hull is computed **every frame** by fdny.exe  
✔ It depends on player state (standing, crouching, ladder, etc.)  
✔ It lives in fdny.exe memory **before** Genesis.dll is called  
✔ Genesis.dll never owns the authoritative data  

---

## How to Proceed From Here

### Recommended Next Steps

1. **Set write breakpoints** on `+0xEE4 / +0xEE8 / +0xEEC`
2. Identify:
   - Writing instruction
   - Base register (EBP / ESP / ESI / ECX)
3. Determine whether this is:
   - A player struct field, or
   - A stack-local movement frame
4. Map nearby offsets to reconstruct the full collision hull:
   - Radius / width
   - Depth
   - Full Min/Max vectors

---

## Final Conclusion

> There is **no persistent player collision hull stored in Genesis.dll or actor memory**.
>
> The **only real collision bounds** are dynamically computed by fdny.exe and exist briefly in its movement state memory — exactly where offsets like `EE4 / EE8 / EEC` were found.

This explains all previous contradictions and confirms the correct layer to monitor or modify for collision behavior.

---
