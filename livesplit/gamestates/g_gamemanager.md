# GameManager Structure Analysis

## What is `g_GameManager`?

`g_GameManager` is a **global pointer** (not an array or struct itself) that points to a GameManager struct/object.

### Evidence from Code:

- **`GameManager_Constructor`** shows: `g_GameManager = param_1;`
- **`GameManager_Create`** allocates `0x40 bytes` (64 bytes) for the GameManager object
- `g_GameManager` is set to point to this allocated memory

**Conclusion:** `g_GameManager` is a pointer to a GameManager structure/object.

---

## What does `g_GameManager[0xc]` mean?

In the decompiled C code, `g_GameManager[0xc]` uses array indexing notation, but since `g_GameManager` is a pointer, this is equivalent to:
```c
*(g_GameManager + 0xc)   // Pointer arithmetic
```

This accesses the memory at offset `0xc` (12 in decimal) from where `g_GameManager` points.

### Important Clarification:

Since each array element is **4 bytes** (on a 32-bit system), `g_GameManager[0xc]` actually means:

- Offset `0xc × 4 bytes = 0x30 bytes` (48 bytes) from the start of the GameManager structure

---

## What value is stored there?

From `GameManager_InitializeSubsystems`, we see:
```c
g_GameManager[0xc] = FUN_0049d130();  // Returns a pointer to some subsystem
```

**So `g_GameManager[0xc]` stores a pointer to another subsystem object** (likely a game state/logic manager).

---

## How to find what values it may have:

### 1. Look at initialization code
In `GameManager_InitializeSubsystems`, the value is set to the return value of `FUN_0049d130()`

### 2. Look at all writes to `g_GameManager[0xc]`
Search for cross-references to this location

### 3. Look at reads
In your `RescueBot_Update` function, it reads this value and uses it to access game state information at various offsets:
- `0x18c` - Game state
- `0x3530` - Victim count
- `0x5f4` - Message display system

---

## Summary

| Component | Description |
|-----------|-------------|
| `g_GameManager` | Global pointer to a GameManager object |
| `g_GameManager[0xc]` | The pointer stored at offset `0x30` (48 bytes) within the GameManager structure |
| The struct at `g_GameManager[0xc]` | A game subsystem object (likely GameState or GameLogic) that contains: |

### Subsystem Structure (at `g_GameManager[0xc]`):

| Offset | Description |
|--------|-------------|
| `+0x18c` | Game state value |
| `+0x3530` | Victim count |
| `+0x5f4` | Message display system |

---

## Key Insight

The `[0xc]` is **array notation for pointer arithmetic**—it's accessing a field within the GameManager struct that itself is a pointer to another object.
```c
// Memory layout visualization
GameManager* g_GameManager;  // Global pointer

// GameManager structure (64 bytes allocated)
struct GameManager {
    void* field_0x00;
    void* field_0x04;
    void* field_0x08;
    void* subsystem_0x0c;  // <- This is g_GameManager[0xc] (at offset 0x30 bytes)
    // ... more fields ...
};

// The subsystem at g_GameManager[0xc] has its own structure:
struct GameSubsystem {
    // ... various fields ...
    int gameState;        // At offset +0x18c
    // ... more fields ...
    int victimCount;      // At offset +0x3530
    // ... more fields ...
    void* messageSystem;  // At offset +0x5f4
};

// Usage example:
void* subsystem = g_GameManager[0xc];  // or *(g_GameManager + 0xc)
int gameState = *(int*)((int)subsystem + 0x18c);
int victimCount = *(int*)((int)subsystem + 0x3530);
```