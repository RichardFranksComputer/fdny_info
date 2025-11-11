# 🎯 FINDINGS SUMMARY

## **Console Log Memory Location**

**Address:** `0x00502A44` (g_CurrentLogEntry + 0x10)
- **Type:** DWORD pointer to text buffer
- **Usage:** This pointer value updates when new console messages are logged
- **CheatEngine:** Add as 4-byte/DWORD type, follow the pointer value to read the text string

---

## **TChatterSet Sound System**

### **Core Functions:**
- **TChatterSet_PlayShuffledSound** (0x00489110) - Plays randomized sound, logs "[TChatterSet] Playing shuffled sound: {filename}"
- **TChatterSet_PlaySound** (referenced but not decompiled) - Standard sound playback
- **LogSystem_Submit** (0x00422060) - Central logging hub, writes to g_CurrentLogEntry
- **LogEntry_GetTextBufferPointer** (0x004a2c03) - Extracts text pointer from LogEntry at offset +0x10

### **Call Chain to TChatterSet_PlayShuffledSound:**

**1. GameState_HandleSurvivorEvent (0x004571a0)**
   - **When:** param_1 == 1 (survivor pickup event)
   - **Plays:** "RC_VictPick" via TChatterSet_PlaySound
   - **Code:**
   ```c
   String_Construct(&local, "RC_VictPick");
   TChatterSet_PlaySound(this+0x3540, piVar1, true);
When: param_1 == 2 (survivor drop event) AND survivors remain
Plays: "RC_VictDrop" via TChatterSet_PlaySound
Code:
String_Construct(&local, "RC_VictDrop");
TChatterSet_PlaySound(this+0x3540, piVar3, true);
2. Character_TakeDamage (0x00451640)
When: Character takes burn/fire damage
Plays: "RC_Pain" via TChatterSet_PlaySound (with cooldown)
Code:
String_Construct(&local, "RC_Pain");
TChatterSet_PlaySound(this+0x3540, piVar6, false);
Evidence of Sound Overlaying:
YES - Two sounds can overlay:
Scenario 1: Survivor Pickup
GameState_HandleSurvivorEvent(param_1=1) is called
Plays "RC_VictPick" chatter sound immediately
If this triggers TChatterSet_PlayShuffledSound internally, both sounds play simultaneously
Scenario 2: Damage While Carrying Survivor
Character_TakeDamage plays "RC_Pain" sound
If GameState_HandleSurvivorEvent is triggered simultaneously, "RC_VictPick" or "RC_VictDrop" plays
Both chatter sounds overlap
Scenario 3: Drop Survivor with Remaining Survivors
GameState_HandleSurvivorEvent(param_1=2) checks if survivors remain
If true, plays "RC_VictDrop" sound
This could overlay with win condition sounds or other game audio
 
Renamed Functions:
GameState_HandleSurvivorEvent (0x004571a0) - Handles survivor pickup/drop events, plays RC_VictPick/RC_VictDrop
Character_TakeDamage (0x00451640) - Damage handler, plays RC_Pain
TChatterSet_PlayShuffledSound (0x00489110) - Randomized sound playback with console logging
LogSystem_Submit (0x00422060) - Central log submission
LogEntry_GetTextBufferPointer (0x004a2c03) - Gets text from LogEntry+0x10
LogEntry_AppendText (0x004a3a
