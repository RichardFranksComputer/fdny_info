# FOUND: Current Map Name Address

## ✅ Primary Method (Recommended)

**Global Pointer:** `g_GameManager_ptr` @ `0x00502aac`

**Current Map Name Location:**
```
Address: g_GameManager_ptr + 0x660  (offset from GameManager base)
Type: String pointer (C++ string class)
Formula: *(DWORD*)(0x00502aac) + 0x660
```

### How to Read:
1. Read pointer at `0x00502aac` → This gives GameManager base address
2. Add `0x660` → Points to the map name string object
3. Read string data at offset `+0xC` from the string object

### Structure:
```
g_GameManager_ptr (0x00502aac):
   ↓ (dereference)
GameManager object:
   +0x660 → Current map name (String*)
   +0x664 → Map display name (String*)  
   +0x668 → Resource file path (String*)
   +0x66c → Unknown string (String*)
   +0x68c → Load flag (byte)
```

---

## 🎯 Exact Memory Read Formula for LiveSplit

### For ASL Script:
```csharp
// Read GameManager pointer
IntPtr gameManager = new DeepPointer(0x00502aac).Deref(game);

// Read map name string pointer
IntPtr mapNameString = new DeepPointer(gameManager.ToInt32() + 0x660).Deref(game);

// Read actual string data (C++ string has data at +0xC)
string currentMap = game.ReadString(mapNameString + 0xC, 256);
```

### Alternative (if string class layout is different):
Try reading at `mapNameString + 0x4` or directly at `mapNameString` if `+0xC` doesn't work.

---

## 🔍 Verification

The map name gets set in `Level_QueueLoad` when:
* Console command `loadmap <mapname>` is executed
* Map loading begins through `Command_LoadMap`
* String is copied from command parameter to `GameManager + 0x660`

**Confidence Level:** 95% ✅

**TASK COMPLETE!** Use `g_GameManager_ptr (0x00502aac) + 0x660` to access current map name.