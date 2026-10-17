# BoundsTrigger Structure Definitions

## BoundsTriggerUserdata (68 bytes / 0x44)

| Offset | Type   | Field Name        | Description                              |
|--------|--------|-------------------|------------------------------------------|
| +0x00  | void*  | vtable_or_typeinfo| Standard object layout                   |
| +0x04  | char*  | szTriggerName     | Passed to SetEntityName                  |
| +0x08  | int    | modelId           | Model ID                                 |
| +0x0C  | int    | triggerType       | Trigger type, copied to wrapper+0x160    |
| +0x10  | char*  | szEventScript1    | Passed to RegisterEventOrScript          |
| +0x14  | char*  | szEventScript2    | Passed to RegisterEventOrScript          |
| +0x18  | char*  | szEventScript3    | Passed to RegisterEventOrScript          |
| +0x1C  | char*  | szEventScript4    | Passed to RegisterEventOrScript          |
| +0x20  | char*  | szEventScript5    | Passed to RegisterEventOrScript          |
| +0x24  | char*  | szEventScript6    | Passed to RegisterEventOrScript          |
| +0x28  | char*  | szEventScript7    | Passed to RegisterEventOrScript          |
| +0x2C  | char*  | szEventScript8    | Passed to RegisterEventOrScript          |
| +0x30  | char*  | szEventScript9    | Passed to RegisterEventOrScript          |
| +0x34  | char*  | szEventScript10   | Passed to RegisterEventOrScript          |
| +0x38  | float  | fBoundX           | Width of trigger volume                  |
| +0x3C  | float  | fBoundY           | Height of trigger volume                 |
| +0x40  | float  | fBoundZ           | Depth of trigger volume                  |

---

## RCS_BoundsTrigger Wrapper (360 bytes / 0x168)

| Offset | Type                    | Field Name         | Description                                |
|--------|-------------------------|--------------------|--------------------------------------------|
| +0x00  | void*                   | vtable             | Vtable pointer                             |
| +0x04  | char[0x14]              | baseData1          | Unknown base class data (20 bytes)         |
| +0x18  | int                     | objectType         | Set to 0x8 in constructor                  |
| +0x1C  | char[0x08]              | unknown1           | Unknown (8 bytes)                          |
| +0x24  | char[0x7C]              | baseObject         | Embedded base object (124 bytes)           |
| +0xA0  | char[0x28]              | stringContainer    | Object holding strings (40 bytes)          |
| +0xC8  | float                   | fBoundX            | Copied from userdata+0x38                  |
| +0xCC  | float                   | fBoundY            | Copied from userdata+0x3C                  |
| +0xD0  | float                   | fBoundZ            | Copied from userdata+0x40                  |
| +0xD4  | char[0x10]              | unknown2           | Unknown (16 bytes)                         |
| +0xE4  | char[0x18]              | transformObject    | Initialized by FUN_00481950 (24 bytes)     |
| +0xFC  | BoundsTriggerUserdata*  | pUserdata          | Pointer to userdata                        |
| +0x100 | char[0x18]              | collectionObject   | Initialized by FUN_00490270 (24 bytes)     |
| +0x118 | char[0x48]              | unknownObject      | Initialized by FUN_004b9674 (72 bytes)     |
| +0x160 | int                     | triggerTypeCache   | Copied from userdata+0xC                   |
| +0x164 | byte                    | bTriggeredFlag     | 0 = inactive, 1 = triggered                |
| +0x165 | byte                    | bStateFlag         | Secondary state flag, initialized to 0     |
| +0x166 | byte[0x02]              | padding            | Padding (2 bytes)                          |

---

## Key Relationships

- **Userdata Access**: Wrapper+0xFC points to BoundsTriggerUserdata
- **Bounds Storage**: Userdata bounds (+0x38/3C/40) copied to wrapper (+0xC8/CC/D0)
- **Trigger Type**: Userdata+0x0C copied to wrapper+0x160
- **Event Handlers**: 10 string pointers in userdata (+0x10 through +0x34)
- **State Tracking**: Wrapper flags at +0x164 (triggered) and +0x165 (state)