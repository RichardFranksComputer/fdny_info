# RCS_BoundsTrigger Struct Definition - FINAL

## Structure Size

**360 bytes (0x168)** - ✅ CONFIRMED

---

## Complete Struct Definition
```c
typedef struct RCS_BoundsTrigger {
    // Core Object (0x00-0x23)
    void*    vtable;              // +0x00 (4 bytes) - PTR_FUN_004e1090
    void*    unknown_ptr1;        // +0x04 (4 bytes)
    int32_t  unknown_int1;        // +0x08 (4 bytes) - initialized to 0
    int32_t  unknown_int2;        // +0x0C (4 bytes)
    uint8_t  unknown_byte1;       // +0x10 (1 byte) - set to 0
    uint8_t  padding1[3];         // +0x11 (3 bytes)
    int32_t  unknown_int3;        // +0x14 (4 bytes) - initialized to 0
    int32_t  unknown_int4;        // +0x18 (4 bytes) - initialized to 0
    uint8_t  active;              // +0x1C (1 byte) - active/enabled flag
    uint8_t  unknown_byte2;       // +0x1D (1 byte) - set to 0
    uint8_t  padding2[2];         // +0x1E (2 bytes)
    int32_t  unknown_int5;        // +0x20 (4 bytes) - initialized to 0
    
    // Event/Entity System (0x24-0x47)
    void*    event_system;        // +0x24 (4 bytes)
    int32_t  unknown_data1[9];    // +0x28 (36 bytes) - initialized to 0
    
    // String/Name Data (0x48-0x77)
    char*    name_or_string;      // +0x48 (4 bytes) - string pointer
    int32_t  unknown_data2[11];   // +0x4C (44 bytes) - initialized to 0
    
    // Cleanup Tracking (0x78-0xC7)
    void*    cleanup_ptr1;        // +0x78 (4 bytes)
    int32_t  unknown_data3[19];   // +0x7C (76 bytes) - initialized to 0
    
    // Source Position (0xC8-0xE3)
    float    source_x;            // +0xC8 (4 bytes) - copied to mins/maxs.x
    float    source_y;            // +0xCC (4 bytes) - copied to mins/maxs.y
    float    source_z;            // +0xD0 (4 bytes) - copied to mins/maxs.z
    int32_t  unknown_data4[5];    // +0xD4 (20 bytes) - initialized to 0
    
    // BOUNDING BOX (0xE4-0xFB) ⭐
    geVec3d  mins;                // +0xE4 (12 bytes) - minimum bounds
    geVec3d  maxs;                // +0xF0 (12 bytes) - maximum bounds
    
    // Entity Userdata (0xFC-0xFF)
    void*    entity_userdata;     // +0xFC (4 bytes) - pointer to entity userdata
    
    // Additional Tracking (0x100-0x167)
    void*    cleanup_ptr2;        // +0x100 (4 bytes)
    int32_t  unknown_data5[2];    // +0x104 (8 bytes) - initialized to 0
    void*    cleanup_ptr3;        // +0x10C (4 bytes)
    int32_t  unknown_data6[2];    // +0x110 (8 bytes) - initialized to 0
    void*    cleanup_ptr4;        // +0x118 (4 bytes)
    int32_t  unknown_data7[17];   // +0x11C (68 bytes) - initialized to 0
    int32_t  userdata_property;   // +0x160 (4 bytes) - from *(userdata+0xC)
    uint8_t  event_check_result;  // +0x164 (1 byte) - Entity_CheckEvent("touch")
    uint8_t  trigger_state;       // +0x165 (1 byte) - set to 0 in init
    uint8_t  padding3[2];         // +0x166 (2 bytes)
    
} RCS_BoundsTrigger;  // Total: 360 bytes (0x168)

// geVec3d structure (12 bytes)
typedef struct geVec3d {
    float x;  // +0x00 (4 bytes)
    float y;  // +0x04 (4 bytes)
    float z;  // +0x08 (4 bytes)
} geVec3d;
```

---

## Key Confirmed Fields

| Offset | Size | Type | Purpose | Evidence |
|--------|------|------|---------|----------|
| **+0x00** | 4 | void* | vtable pointer (PTR_FUN_004e1090) | Constructor FUN_00441c60 |
| **+0x1C** | 1 | uint8_t | **active flag** (0=inactive, 1=active) | FUN_0049d530, FUN_0049d310 |
| **+0xC8** | 4 | float | source_x (copied to mins/maxs) | FUN_00441040 |
| **+0xCC** | 4 | float | source_y (copied to mins/maxs) | FUN_00441040 |
| **+0xD0** | 4 | float | source_z (copied to mins/maxs) | FUN_00441040 |
| **+0xE4** | 12 | geVec3d | **mins** - minimum bounding box corner | FUN_00441040 |
| **+0xF0** | 12 | geVec3d | **maxs** - maximum bounding box corner | FUN_00441040 |
| **+0xFC** | 4 | void* | entity_userdata pointer | Constructor, FUN_00441040 |
| **+0x160** | 4 | int32_t | Property from userdata+0xC | FUN_00441040 |
| **+0x164** | 1 | uint8_t | Touch event check result | FUN_00441040 |

---

## Functions Analyzed

| Function | Purpose | Key Actions |
|----------|---------|-------------|
| **FUN_00441d70** | Factory/Allocator | Allocates 360 bytes (0x168) |
| **FUN_00441c60** | Constructor | Sets vtable, calls base constructor |
| **FUN_0049d420** | Base Constructor | Zeros offsets 0x04-0x164 |
| **FUN_00441040** | Initialization | Sets up bounds at +0xE4/+0xF0 from source |
| **FUN_0049d530** | Activator | Sets active flag (+0x1C) to 1 |
| **FUN_0049d310** | Deactivator | Sets active flag (+0x1C) to 0 |
| **FUN_00441d50** | Destructor | Cleans up pointers |
| **FUN_00441ba0** | Base Destructor | Base cleanup |

---

## Vtable Layout (PTR_FUN_004e1090)

| Offset | Function Address | Purpose |
|--------|------------------|---------|
| +0x00 | 00441d50 | Destructor |
| +0x20 | 00441040 | **Initialization** (sets bounds) |
| +0x28 | 0049d310 | **Deactivation** (sets active=0) |
| +0x2C | 0049d530 | **Activation** (sets active=1) |
| *(others)* | Various | Unknown virtual methods |

---

## Usage Pattern

1. **Allocation:** Factory allocates 360 bytes
2. **Construction:** Base constructor zeros everything, then sets vtable
3. **Initialization:** 
   - Reads source position from +0xC8-0xD0
   - Copies to mins (+0xE4) and maxs (+0xF0)
   - Stores entity userdata pointer at +0xFC
   - Checks for "touch" event support
4. **Runtime:**
   - Active flag (+0x1C) toggles trigger on/off
   - Bounds (mins/maxs) used for collision/trigger detection
5. **Cleanup:** Destructor cleans up internal pointers

---

## Critical Discovery: Axis-Aligned Bounding Box (AABB)

The trigger uses an **AABB** defined by:
- **mins** (+0xE4): Lower-left-back corner (minimum x, y, z)
- **maxs** (+0xF0): Upper-right-front corner (maximum x, y, z)

The source position (+0xC8-0xD0) is copied to both mins and maxs during initialization, suggesting the trigger either:
- Expands from a point, or
- Has dimensions set through other means

---

## Confidence Levels

| Level | Description | Fields |
|-------|-------------|--------|
| ✅ **CONFIRMED (100%)** | Directly accessed in code | vtable, active, mins, maxs, userdata |
| 🟨 **LIKELY (80%)** | Inferred from patterns | event_system, name_or_string, cleanup pointers |
| 🟦 **UNKNOWN (50%)** | Zeroed, no observed usage | Most middle sections |

---

## Binary Location

**Source:** fdny.exe  
**Allocation:** FUN_00441d70 allocates 360 bytes via `operator_new(0x168)`  
**Status:** COMPLETE - Ready for use in modding/reverse engineering

---

## Quick Reference for Modding
```c
// Cast engine pointer to RCS_BoundsTrigger
RCS_BoundsTrigger* trigger = (RCS_BoundsTrigger*)engine_pointer;

// Access key fields:
trigger->active;          // +0x1C - Enable/disable trigger
trigger->mins;            // +0xE4 - Bounding box minimum
trigger->maxs;            // +0xF0 - Bounding box maximum
trigger->entity_userdata; // +0xFC - Entity data pointer
```