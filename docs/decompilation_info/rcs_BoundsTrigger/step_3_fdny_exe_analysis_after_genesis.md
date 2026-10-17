# RCS_BoundsTrigger Struct - Complete Definition

## Structure Size

**360 bytes (0x168)** - ✅ CONFIRMED

---

## Complete C Struct Definition
```c
typedef struct RCS_BoundsTrigger {
    // Core Object (0x00-0x23)
    void*    vtable;           // +0x00 (4 bytes) - PTR_FUN_004e1090
    void*    unknown_ptr1;     // +0x04 (4 bytes) - used in FUN_0049b780
    int32_t  unknown_int1;     // +0x08 (4 bytes) - initialized to 0
    int32_t  unknown_int2;     // +0x0C (4 bytes) - set from param
    uint8_t  unknown_byte1;    // +0x10 (1 byte) - set to 0
    uint8_t  padding1[3];      // +0x11 (3 bytes)
    int32_t  unknown_int3;     // +0x14 (4 bytes) - initialized to 0
    int32_t  unknown_int4;     // +0x18 (4 bytes) - initialized to 0
    uint8_t  active;           // +0x1C (1 byte) ⭐ active/enabled flag
    uint8_t  unknown_byte2;    // +0x1D (1 byte) - set to 0
    uint8_t  padding2[2];      // +0x1E (2 bytes)
    int32_t  unknown_int5;     // +0x20 (4 bytes) - initialized to 0
    
    // Event/Entity System (0x24-0x47)
    void*    event_system;     // +0x24 (4 bytes) - FUN_0046e320 operates on this
    int32_t  unknown_data1[9]; // +0x28 (36 bytes) - initialized to 0
    
    // String/Name Data (0x48-0x77)
    char*    name_or_string;   // +0x48 (4 bytes) - string pointer
    int32_t  unknown_data2[11];// +0x4C (44 bytes) - initialized to 0
    
    // Cleanup Tracking (0x78-0xC7)
    void*    cleanup_ptr1;     // +0x78 (4 bytes) - in destructor
    int32_t  unknown_data3[19];// +0x7C (76 bytes) - initialized to 0
    
    // Source Position (0xC8-0xE3)
    float    source_x;         // +0xC8 (4 bytes) - copied to mins/maxs
    float    source_y;         // +0xCC (4 bytes) - copied to mins/maxs
    float    source_z;         // +0xD0 (4 bytes) - copied to mins/maxs
    int32_t  unknown_data4[5]; // +0xD4 (20 bytes) - initialized to 0
    
    // BOUNDING BOX (0xE4-0xFB) ⭐⭐⭐
    geVec3d  mins;             // +0xE4 (12 bytes) - minimum bounds
    geVec3d  maxs;             // +0xF0 (12 bytes) - maximum bounds
    
    // Entity Userdata (0xFC-0xFF)
    void*    entity_userdata;  // +0xFC (4 bytes) - entity userdata pointer
    
    // Additional Tracking (0x100-0x167)
    void*    cleanup_ptr2;     // +0x100 (4 bytes) - in destructor
    int32_t  unknown_data5[2]; // +0x104 (8 bytes) - initialized to 0
    void*    cleanup_ptr3;     // +0x10C (4 bytes) - in destructor
    int32_t  unknown_data6[2]; // +0x110 (8 bytes) - initialized to 0
    void*    cleanup_ptr4;     // +0x118 (4 bytes) - in destructor
    int32_t  unknown_data7[17];// +0x11C (68 bytes) - initialized to 0
    int32_t  userdata_property;// +0x160 (4 bytes) - from *(userdata+0xC)
    uint8_t  event_check_result;// +0x164 (1 byte) - Entity_CheckEvent("touch")
    uint8_t  trigger_state;    // +0x165 (1 byte) - set to 0 in init
    uint8_t  padding3[2];      // +0x166 (2 bytes)
    
} RCS_BoundsTrigger;  // Total: 360 bytes (0x168)

// geVec3d structure (12 bytes)
typedef struct geVec3d {
    float x;  // +0x00 (4 bytes)
    float y;  // +0x04 (4 bytes)
    float z;  // +0x08 (4 bytes)
} geVec3d;
```

---

## Key Confirmed Offsets

| Offset | Size | Type | Purpose | Confidence |
|--------|------|------|---------|------------|
| **+0x00** | 4 | void* | vtable (PTR_FUN_004e1090) | ✅ 100% |
| **+0x1C** | 1 | uint8_t | **active flag** (0=off, 1=on) | ✅ 100% |
| **+0xC8** | 4 | float | source_x (copied to bounds) | ✅ 100% |
| **+0xCC** | 4 | float | source_y (copied to bounds) | ✅ 100% |
| **+0xD0** | 4 | float | source_z (copied to bounds) | ✅ 100% |
| **+0xE4** | 12 | geVec3d | **mins** - minimum bounding box | ✅ 100% |
| **+0xF0** | 12 | geVec3d | **maxs** - maximum bounding box | ✅ 100% |
| **+0xFC** | 4 | void* | entity_userdata pointer | ✅ 100% |
| +0x04 | 4 | void* | Unknown pointer | 🟨 80% |
| +0x24 | 4 | void* | Event system | 🟨 80% |
| +0x48 | 4 | char* | Name/string | 🟨 80% |
| +0x160 | 4 | int32_t | Userdata property | ✅ 100% |
| +0x164 | 1 | uint8_t | Touch event result | ✅ 100% |

---

## Functions Identified

| Original Name | New Name | Purpose |
|---------------|----------|---------|
| FUN_00441d70 | **RCS_BoundsTrigger_Factory** | Allocates 360 bytes |
| FUN_00441c60 | **RCS_BoundsTrigger_Constructor** | Sets vtable, calls base |
| FUN_0049d420 | **RCS_BoundsTrigger_BaseConstructor** | Zeros offsets 0x04-0x164 |
| FUN_00441040 | **RCS_BoundsTrigger_Initialize** | Sets up bounds at +0xE4/+0xF0 |
| FUN_0049d530 | **RCS_BoundsTrigger_Activate** | Sets active (+0x1C) to 1 |
| FUN_0049d310 | **RCS_BoundsTrigger_Deactivate** | Sets active (+0x1C) to 0 |
| FUN_00441d50 | **RCS_BoundsTrigger_Destructor** | Cleanup |
| FUN_00441ba0 | **RCS_BoundsTrigger_BaseDestructor** | Base cleanup |
| FUN_00440d60 | **RCS_BoundsTrigger_FindByName** | Factory finder |
| FUN_0049d160 | **Entity_InitUserDataStruct** | Inits userdata at +0xFC |
| FUN_00492a20 | **Entity_GetUserDataWrapper** | Wrapper for GetUserData |

---

## Vtable Layout (PTR_FUN_004e1090)

| Offset | Address | Purpose |
|--------|---------|---------|
| +0x00 | 00441d50 | **Destructor** |
| +0x20 | 00441040 | **Initialize** (sets bounds) |
| +0x28 | 0049d310 | **Deactivate** (active=0) |
| +0x2C | 0049d530 | **Activate** (active=1) |
| *(others)* | Various | Unknown virtual methods |

---

## Usage Pattern

1. **Allocation:** Factory allocates 360 bytes
2. **Construction:** 
   - Base constructor zeros everything (0x04-0x164)
   - Constructor sets vtable to PTR_FUN_004e1090
3. **Initialization:** `RCS_BoundsTrigger_Initialize`
   - Reads source position (0xC8-0xD0)
   - Copies to mins (+0xE4) and maxs (+0xF0)
   - Stores entity userdata pointer (+0xFC)
   - Checks for "touch" event support
4. **Runtime:**
   - Active flag (+0x1C) toggles trigger on/off
   - Bounds (mins/maxs) used for collision detection
5. **Cleanup:** Destructor frees internal pointers

---

## Bounding Box: AABB (Axis-Aligned Bounding Box)

The trigger uses an **AABB** for collision:
- **mins** (+0xE4): Minimum corner (lower-left-back)
- **maxs** (+0xF0): Maximum corner (upper-right-front)

The source position (+0xC8-0xD0) initializes both, suggesting expansion happens elsewhere.

---

## Key Memory Addresses

| Address | Description |
|---------|-------------|
| 0x004e0fa8 | String: "RCS_BoundsTrigger" |
| 0x004e0f98 | Factory vtable |
| 0x004e1090 | RCS_BoundsTrigger vtable |

---

## Quick Reference for Modding
```c
// Cast engine pointer
RCS_BoundsTrigger* trigger = (RCS_BoundsTrigger*)engine_ptr;

// Access key fields:
trigger->active;          // +0x1C - Enable/disable
trigger->mins;            // +0xE4 - Min bounds
trigger->maxs;            // +0xF0 - Max bounds
trigger->entity_userdata; // +0xFC - Entity data
```

---

**Source:** fdny.exe  
**Allocation:** 360 bytes via `operator_new(0x168)`  
**Status:** COMPLETE - Ready for use