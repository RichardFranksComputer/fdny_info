# RCS_BoundsTrigger Reverse Engineering - genesis.dll Results

## Critical Finding

⚠️ **RCS_BoundsTrigger is NOT defined in genesis.dll**

The entity class "RCS_BoundsTrigger" does not exist in the engine DLL. It's a **custom entity class** registered by the game executable (fdny.exe).

---

## What Was Found in genesis.dll

### Entity System Architecture

**Entity Registration System:**
- Entity classes stored in linked list at `EntitySet + 0x10`
- Each entity class node structure:
```c
  struct EntityClassNode {
      char* className;      // +0x00
      // ... unknown fields
      int   userDataSize;   // +0x10
      EntityClassNode* next; // +0x14
  };
```

**Entity Data Access:**
- User data pointer stored at `geEntity + 0x08`
- Retrieved via `geEntity_GetUserData(entity)` → returns `void*`
- Size queried via `geEntity_GetUserDataSizeForClass(className)` → returns size from linked list

---

### geVec3d Structure - CONFIRMED
```c
typedef struct geVec3d {
    float X;  // +0x00 (4 bytes)
    float Y;  // +0x04 (4 bytes)
    float Z;  // +0x08 (4 bytes)
} geVec3d;    // Total: 12 bytes
```

**Evidence:**
- Analyzed `geBody_GetBoundingBox` and `geBody_SetBoundingBox`
- Both functions copy 12 bytes for mins and 12 bytes for maxs
- **geVec3d = 12 bytes (3 × 4-byte floats), NOT 24 bytes**

---

### Standard Bounding Box Pattern

From engine functions that handle bounding boxes:
```c
// Standard bounding box layout in genesis.dll
struct BoundingBox {
    geVec3d mins;  // 12 bytes
    geVec3d maxs;  // 12 bytes
};  // Total: 24 bytes
```

---

## Key Functions Analyzed

| Function | Purpose | Key Information |
|----------|---------|----------------|
| **geEntity_GetUserDataSizeForClass** | Returns entity class size | Searches linked list by className, returns size at +0x10 |
| **geEntity_GetUserData** | Gets entity data pointer | Returns void* at entity+0x08 |
| **geBody_GetBoundingBox** | Retrieves bounding box | Confirms geVec3d=12 bytes, standard mins/maxs layout |
| **geBody_SetBoundingBox** | Sets bounding box | Confirms geVec3d=12 bytes, standard mins/maxs layout |
| **geWorld_GetEntitySet** | Gets entity set by name | Entity class list stored at EntitySet+0x10 |

---

## Best-Effort Struct Reconstruction

Based on engine patterns (NOT found directly in genesis.dll):
```c
// STRUCT SIZE: UNKNOWN - Custom entity class not in genesis.dll
// CONFIDENCE: EDUCATED GUESS based on engine bounding box patterns

typedef struct RCS_BoundsTrigger {
    geVec3d mins;    // +0x00 (12 bytes) - Minimum bounds
    geVec3d maxs;    // +0x0C (12 bytes) - Maximum bounds  
    int     active;  // +0x18 (4 bytes)  - Active/enabled flag
    // ... possibly more members
} RCS_BoundsTrigger;
// Minimum size: 28 bytes (24 for bounds + 4 for flag)
```

**Rationale:**
- Standard engine pattern: mins/maxs pairs
- geVec3d confirmed as 12 bytes each
- Active flag is common for trigger entities
- **Actual size and additional members UNKNOWN**

---

## What Wasn't Found

❌ "RCS_BoundsTrigger" string anywhere in genesis.dll  
❌ Entity class size for RCS_BoundsTrigger  
❌ Any RCS_BoundsTrigger-specific code  
❌ Actual member offsets beyond mins/maxs pattern  
❌ Function pointers (onEnter/onLeave callbacks)  

**Reason:** Custom entity classes are defined by the game, not the engine.

---

## Architecture Summary
```
┌─────────────────────────┐
│     genesis.dll         │
│  (Game Engine DLL)      │
│                         │
│  • Provides entity API  │
│  • Defines geVec3d      │
│  • Manages entity data  │
│  • Does NOT contain     │
│    RCS_BoundsTrigger    │
└─────────────────────────┘
           ↑
           │ Uses API
           │
┌─────────────────────────┐
│      fdny.exe           │
│  (Game Executable)      │
│                         │
│  • Registers custom     │
│    entity classes       │
│  • Defines              │
│    RCS_BoundsTrigger    │
│  • Stores class size    │
│    in linked list       │
└─────────────────────────┘
```

---

## How to Find the Actual Struct

### Method 1: Runtime Query (Recommended)
```c
int size = geEntity_GetUserDataSizeForClass("RCS_BoundsTrigger");
printf("RCS_BoundsTrigger size: %d bytes\n", size);
```

### Method 2: Analyze fdny.exe
Search for:
- Entity class registration code
- Calls to functions that add entity classes
- The size passed when registering "RCS_BoundsTrigger"

### Method 3: Entity Definition Files
Look for:
- `.ini`, `.cfg`, or custom entity definition files
- Class definitions with size information
- Entity property specifications

### Method 4: Memory Dump
1. Get entity pointer from engine
2. Dump 64-128 bytes
3. Identify patterns (vtable, vectors, flags)

---

## Confirmed Information

| Item | Value | Confidence |
|------|-------|------------|
| geVec3d size | 12 bytes (3 floats) | ✅ 100% |
| geVec3d layout | X, Y, Z (4 bytes each) | ✅ 100% |
| Standard bounding box | mins + maxs (24 bytes) | ✅ 100% |
| Entity user data location | entity + 0x08 | ✅ 100% |
| RCS_BoundsTrigger in genesis.dll | Does not exist | ✅ 100% |
| RCS_BoundsTrigger struct size | Unknown | ❌ 0% |
| RCS_BoundsTrigger member offsets | Unknown | ❌ 0% |

---

## Bottom Line

**genesis.dll provides the entity framework but does not define RCS_BoundsTrigger.** The struct is registered by fdny.exe at runtime. Based on engine bounding box patterns, the struct likely starts with `geVec3d mins` and `geVec3d maxs` (24 bytes), but the exact size and additional members must be determined from the game executable or runtime queries.

---

**Target:** genesis.dll  
**Result:** Engine patterns documented, custom entity not found  
**Status:** RCS_BoundsTrigger definition is in fdny.exe, not genesis.dll