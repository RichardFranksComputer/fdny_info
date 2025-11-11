# Finding Sound Pointers

## Quick Reference

**Pointer chain:** `0x00503A78 -> 8 -> 0 -> 104 -> 0`

**Behavior:**
- Value = 0 (not playing)
- Value = non-zero (playing)

---

## Step-by-Step Process for a NEW Sound

### Phase 1: Find the Sound Buffer Address

1. **Set up memory scanning in Cheat Engine**
   - Trigger your target sound in-game
   - Scan for "Unknown initial value"
   - Trigger sound again
   - Scan for "Changed value"
   - Repeat until you narrow it down

2. **OR - Use a known sound file:**
   - If you know the sound filename, search for references to it
   - The game likely loads it into memory at a specific address

3. **You'll get an address like:** `0x0a902f00` (for the sound we traced)
   - This is the **FMOD sound buffer pointer**
   - Note this address!

---

### Phase 2: Set Up Breakpoints

**In your debugger (x64dbg, Cheat Engine debugger, etc.):**

1. **Breakpoint 1: FMOD.FSOUND_PlaySoundEx**
   - Condition: `ECX == [your_sound_address]`
   - Example: `ECX == 0x0a902f00`
   - This triggers when YOUR specific sound is about to play

2. **Breakpoint 2: 0x004a0d04** (the storage instruction)
   - No condition needed
   - This is where the channel handle gets stored

---

### Phase 3: Capture the SoundChannel Address

1. **Run the game and trigger your sound**

2. **When breakpoint 1 hits:**
   - Note: "Target sound is being loaded"
   - Continue execution

3. **When breakpoint 2 hits (should be right after):**
   - **Record the ESI register value**
   - Example: `ESI = 0x0A9855D0`
   - This is your **SoundChannel object address**

4. **Also record EAX:**
   - Example: `EAX = 0x000031E6`
   - This is the **channel handle** (but it changes every time)

---

### Phase 4: Pointer Scan for the SoundChannel

**In Cheat Engine:**

1. **Add the SoundChannel address manually:**
   - Address: [ESI value from step 3]
   - Type: 4 Bytes
   - Example: `0x0A9855D0`

2. **Right-click → "Pointer scan for this address"**
   - Max level: **4**
   - Save file location: anywhere you want
   - Click OK and wait (might take 1-5 minutes)

3. **Filter the results:**
   - Look for paths where:
     - Base address = `0x00503A78` (g_GameManager)
     - First offset = `8` (SoundSystem pointer)
   
4. **You'll get results like:**
   ```
   8 -> 0 -> 104 -> 0
   8 -> 0 -> 108 -> 0
   8 -> 0 -> 10C -> 0
   8 -> 0 -> 110 -> 0
   etc.
   ```

---

### Phase 5: Test Each Pointer Path

**For each candidate pointer path:**

1. **Add it as a manual pointer in Cheat Engine:**
   - Check "Pointer"
   - Address: `FDNYFirefighter.exe+00103A78` (or just `0x00503A78`)
   - Offsets: [the chain from pointer scan]
   - Type: 4 Bytes

2. **Check the current value:**
   - Does it show a number like `0x000031E6`?
   - Or does it show `0`?
   - Or does it show `???` (broken pointer)?

3. **Test the behavior:**
   - **Without triggering sound:** Is value = 0?
   - **Trigger your target sound:** Does value change to non-zero?
   - **After sound finishes:** Does it go back to 0?

4. **If YES to all three: YOU FOUND IT! ✅**

---

### **Phase 6: Verify Across Game Restart**

**CRITICAL STEP - Don't skip this!**

1. **Note your working pointer path**
   - Example: `8 -> 0 -> 104 -> 0`

2. **Close the game completely**

3. **Reopen the game**

4. **Add the pointer again in Cheat Engine**

5. **Test:**
   - Does it start at 0?
   - Does it change when you trigger the sound?
   - If YES: **You're done!**
   - If NO: The pointer path isn't stable (rare, but possible)

---

## **Quick Troubleshooting**

### **Problem: Pointer scan finds nothing with offset 8**

**Solution:**
- Try max level 5 instead of 4
- Or manually verify the g_GameManager chain still exists:
```
  [0x00503A78] = ?
  [result + 8] = ?