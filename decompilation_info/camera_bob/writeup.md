# Head-Bob / Screen Shake Data Analysis

## Location Analysis

### Base Pointer Chain
```
g_GameManager (0x00503A78) + 0x30 → PlayerController (0x004FF6F0)
PlayerController + 0x3444 → Oscillating Vec3 (Screen Shake / View Bob)
PlayerController + 0x34A4 → CameraController (confirmed at 0x00502B94)
```

### Oscillating Data Offsets

**Relative to PlayerController base (0x004FF6F0):**

| PlayerController Offset | Absolute Address | CheatEngine Pointer | Type | Description |
|------------------------|------------------|---------------------|------|-------------|
| +0x3444 | 0x00502B34 | [[+103A78]+30]+3444 | float | View Bob X / Screen Shake X |
| +0x3448 | 0x00502B38 | [[+103A78]+30]+3448 | float | View Bob Y / Screen Shake Y |
| +0x344C | 0x00502B3C | [[+103A78]+30]+344C | float | View Bob Z / Screen Shake Z |

### Spatial Relationship
- Screen Shake data is **96 bytes (0x60) BEFORE** Camera Controller
- Camera at +0x34A4, Shake at +0x3444
- This suggests shake is applied **ADDITIVELY** to camera position

---

## Conclusions

### 1. Bob Signal Location

**Address:** `PlayerController + 0x3444` (vec3: X, Y, Z components)
- **X component:** +0x3444 (0x00502B34)
- **Y component:** +0x3448 (0x00502B38)
- **Z component:** +0x344C (0x00502B3C)

**Type:** Vec3 (3× float = 12 bytes)

**Range:** Small oscillating values (confirmed oscillating up/down)

**Nature:** Additive offset applied to view/camera

---

### 2. Why posZ Doesn't Bob But posY Does

**Evidence:**
- Camera position fields (0x00502B94 + 0x00/0x04/0x08) show posY oscillating, posZ static
- Screen shake offset is stored SEPARATELY at PlayerController + 0x3444

**Explanation:**

The bob/shake is **NOT written directly** into the camera position fields. Instead:

1. **Base camera position** (posX, posZ, posY at 0x00502B94) is written from the FireRescue entity transform via `CameraTransform_Copy`
2. **Screen shake/bob offset** (vec3 at 0x00502B34) is stored separately at PlayerController+0x3444
3. **Application point:** The shake offset is likely added during view matrix construction or rendering, NOT stored in the camera position itself

**Why posZ doesn't bob:**

The shake offset at +0x3444 (X), +0x3448 (Y), +0x344C (Z) is applied SELECTIVELY or has different magnitudes per axis. The observation that posZ stays static while posY oscillates suggests:

- **Option A:** The shake Y component (+0x3448) has larger amplitude than Z component (+0x344C)
- **Option B:** The shake is applied only to certain axes during render (Y for vertical bob, X for horizontal sway, Z minimal/zero)
- **Option C:** posZ at camera base IS static collision position, while posY includes additive bob

---

### 3. Writer Site(s)

**Primary Writer Function:** UNKNOWN (not yet found)

**However, identified data flow:**

| Address | Usage | Function | Evidence |
|---------|-------|----------|----------|
| 0x00502B34-0x3C | Shake Offset (vec3) | ScreenEffectController | Passed as param to constructor at 0x004368F0 |
| 0x00502B34 | Read for HUD shake | VictimIndicatorUI_UpdatePosition | Adds to victim indicator position: `pos + offset + DAT_00502b30` |

**Constructor Call Pattern:**
```c
FUN_0048ac60((undefined4 *)((int)this + 0x4c), 1, 0x502b34, '\0');
```
This passes 0x502B34 as parameter, suggesting the ScreenEffectController uses this address to read/write shake values.

**Missing Piece:**

The actual UPDATE function that writes oscillating values (likely sin/cos based) to 0x502B34-0x3C was not found. Likely candidates:
- A per-frame physics/update function in ScreenEffectController
- A global effect manager that updates all screen shake offsets
- Triggered by footsteps (step impulse) or continuous walking (sin wave)

---

### 4. Application Point Math

**Partially Reconstructed Formula:**
```c
// Base camera position (written via transform copy)
vec3 camera_base = FireRescueEntity.transform.position;  // At 0x00502B94

// Screen shake offset (oscillates)
vec3 shake_offset = *(vec3*)(PlayerController + 0x3444);  // At 0x00502B34

// Final view position (applied during rendering)
vec3 view_position = camera_base + shake_offset;

// For victim HUD indicators:
vec2 screen_pos = WorldToScreen(victim.pos + shake_offset);
```

**Evidence for additive application:**
- `VictimIndicatorUI_UpdatePosition` explicitly adds shake: `iVar2 = victim.pos + offset + DAT_00502b30`
- Shake stored SEPARATELY from camera position (not overwritten into posY)
- Small oscillating values typical of additive offsets (not absolute positions)

**Why posZ doesn't bob:**
```c
view_position.y = camera_base.y + shake_offset.y;  // Y oscillates (vertical bob)
view_position.z = camera_base.z + shake_offset.z;  // Z static (shake.z ≈ 0 or small)
```

---

### 5. Player vs Camera vs Collision Architecture

| Component | Location | Purpose | Bob Applied? |
|-----------|----------|---------|--------------|
| **Player Collision Position** | FireRescue Entity (+0x12C in PlayerController) | Physics, collision detection | ❌ NO (stable for collision) |
| **Camera Base Position** | CameraController (PlayerController+0x34A4) | Camera tracking target | ❌ NO (copied from entity) |
| **Screen Shake Offset** | PlayerController+0x3444 (vec3) | Visual bob/shake effect | ✅ YES (oscillates) |
| **Final View Position** | Computed at render time | Player's visual perspective | ✅ YES (base + shake) |

**Key Conclusion:** Bob is **visual only** and does NOT affect collision.

**Evidence:**
- Shake offset stored separately (0x3444) from collision position
- Victim UI calculation adds shake to screen position, not world position
- ScreenEffectController holds POINTER to shake data (read-only reference pattern)
- Camera base position is copied from entity transform (which handles physics)

**Collision Box:** Remains stable at the FireRescue entity position. The shake/bob is purely additive at the view layer.

---

## Structure Summary
```
PlayerController (0x004FF6F0) - 13KB+ structure
├── 0x000-0x5F3: [unknown fields]
├── 0x5F4: RescueGame object
├── 0x12C: FireRescue Entity (player collision position)
├── 0x3444: Screen Shake X (float) ← Oscillating
├── 0x3448: Screen Shake Y (float) ← Oscillating
├── 0x344C: Screen Shake Z (float) ← Static/minimal
├── 0x34A4: Camera Controller (160 bytes at 0x00502B94)
│   ├── 0x00: Camera posX
│   ├── 0x04: Camera posZ
│   ├── 0x08: Camera posY
│   └── ... (orientation vectors, etc.)
└── 0x3530: Victim counter
```

**Access Pattern:**
```c
PlayerController* pController = *(PlayerController**)(g_GameManager + 0x30);
vec3 shake = *(vec3*)(pController + 0x3444);
CameraController* camera = (CameraController*)(pController + 0x34A4);
```