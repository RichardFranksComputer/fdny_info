# Structure Analysis: Camera Controller

## Structure Name
`g_CameraController`

## Base Address
`0x00502b94`

## Size
~160+ bytes (0xA0+)

---

## Field Map (Offsets from 0x00502b94)

### Position Data
| Offset | Type | Name | Description |
|--------|------|------|-------------|
| 0x00 | float | posX | Camera X coordinate |
| 0x04 | float | posZ | Camera Z coordinate |
| 0x08 | float | posY | Camera Y coordinate |

### Orientation Vectors
| Offset | Type | Name | Description |
|--------|------|------|-------------|
| 0x0C | float | upVectorX | Camera up vector X component |
| 0x10 | float | upVectorZ | Camera up vector Z component |
| 0x14 | float | upVectorY | Camera up vector Y component |
| 0x18 | float | forwardVectorX | Camera forward/look direction X |
| 0x1C | float | forwardVectorZ | Camera forward/look direction Z |
| 0x20 | float | forwardVectorY | Camera forward/look direction Y |
| 0x24 | float | rightVectorX | Camera right vector X component |
| 0x28 | float | rightVectorZ | Camera right vector Z component |
| 0x2C | float | rightVectorY | Camera right vector Y component |

### Transform/State Data
| Offset | Type | Name | Description |
|--------|------|------|-------------|
| 0x30 | float | heightOffset | Height adjustment for camera |
| 0x48 | float | targetDirectionX | Normalized target direction X |
| 0x4C | float | targetDirectionZ | Normalized target direction Z |
| 0x50 | float | targetDirectionY | Normalized target direction Y |
| 0x54 | uint32_t | stateFlags | Initialization/state flags (bits 1,2 tracked) |

### Target/LookAt Data
| Offset | Type | Name | Description |
|--------|------|------|-------------|
| 0x68 | float | someYCoord | Used in height calculations |
| 0x74 | float | targetPosX | Camera look-at target X |
| 0x78 | float | targetPosZ | Camera look-at target Z |
| 0x7C | float | targetPosY | Camera look-at target Y |

### Collision Test Points
| Offset | Type | Name | Description |
|--------|------|------|-------------|
| 0x84 | float | collisionPoint1_X | First collision ray test point X |
| 0x88 | float | collisionPoint1_Z | First collision ray test point Z |
| 0x8C | float | collisionPoint1_Y | First collision ray test point Y |
| 0x90 | float | collisionPoint2_X | Second collision ray test point X |
| 0x94 | float | collisionPoint2_Z | Second collision ray test point Z (originally listed as velY) |
| 0x98 | float | collisionPoint2_Y | Second collision ray test point Y (originally listed as velZ) |
| 0x9C | float | tempVectorX | Temporary calculation vector X (originally listed as velX) |
| 0xA0 | float | tempVectorZ | Temporary calculation vector Z |
| 0xA4 | float | tempVectorY | Temporary calculation vector Y |

---

## Key Functions Accessing This Structure

### FUN_00448630 (0x00448630) - Main Camera Update
- Calculates orientation vectors (up, forward, right) from rotation data
- Performs collision testing using ray casts
- Updates camera direction based on target position
- Manages state flags for initialization

### FUN_0044b060 (0x0044b060) - Camera Setup/Initialization
- Checks enable flags at offset 0x9C
- Updates camera animation state
- Manages pointers to camera animation structures (offsets 0x58, 0x5C, 0x70, 0x88, 0x8C)
- Applies velocity scaling factors

### FUN_00447890 (0x00447890) - Structure Copy/Transform
- Copies 64-byte transformation data (offsets 0x4 to 0x40)
- Used for matrix operations

### FUN_00447a90 (0x00447a90) - Entity Management
- Creates RCS_FireRescue entities
- References counter at offset -4 (0x00502b90)
- Uses coordinates at different offsets (0x7C, 0x80, 0x84)

### FUN_00448550 (0x00448550) - Counter Management
- Decrements counter at 0x00502b90 when conditions met

---

## Conclusion: Camera Controller

**This is definitively a CAMERA CONTROLLER structure, not a FireRescue/Player entity.**

### Evidence Supporting Camera Controller:

1. **Orthonormal Basis Vectors**: The structure contains a complete set of orientation vectors (up, forward, right) at offsets 0x0C-0x2C. These form an orthonormal basis typical of camera/view matrices used for rendering transformations.

2. **LookAt/Target System**: Multiple fields dedicated to target tracking (offsets 0x48-0x50, 0x74-0x7C) indicate this is a camera that follows or looks at specific points in the world.

3. **Collision Ray Testing**: The structure contains TWO sets of collision test points (offsets 0x84-0x98), which is characteristic of camera systems that perform ray casts to prevent clipping through geometry or walls.

4. **Height Offset Calculations**: Offset 0x30 stores a height adjustment value computed from terrain/geometry, typical of third-person cameras that maintain distance from ground.

5. **Function Context**: The main update function (FUN_00448630) performs:
   - Cross product calculations for basis vectors
   - Normalization of direction vectors
   - Collision detection with world geometry
   - These are all standard camera controller operations

6. **Single Global Instance**: All XREFs treat this as a singleton global variable (g_Camera*), not an entity in a pool. Player/entity structures are typically instantiated in arrays or pools.

7. **Animation System Integration**: References to camera animation pointers (offsets 0x58, 0x5C, 0x88, 0x8C) and animation arrays suggest this controls cinematic camera movements.

### Why NOT a Player/FireRescue Entity:

- Player entities would have health, inventory, equipment states - none found
- The "velocity" fields at 0x94-0x9C are actually collision test points, not physics velocity
- The RCS_FireRescue references in FUN_00447a90 show those are SEPARATE entities that this camera can track/follow
- No character controller data (grounded state, jump state, animation state machine)

### Final Assessment:

This is the **global third-person camera controller** for the FDNY Firefighter game. It follows player/entity positions, maintains proper orientation through basis vectors, avoids geometry collision, and supports both gameplay and cinematic camera modes through its animation system.

---

## Notes

- Original specification listed offsets 0x94, 0x98, 0x9C as velocity X/Y/Z, but analysis reveals these are actually collision test points and temporary vectors used in camera calculations
- Structure likely extends beyond 0xA4 with additional camera animation and state management fields
- Counter at offset -4 (0x00502b90) tracks FireRescue entity instances