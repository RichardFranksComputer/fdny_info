# Console commands

Commands were found via:

- `strings FDNYFIREFIGHTER.exe | grep -C 50 -i playsnd`

- decompiling .exe in Ghidra and searching `playsnd`

# Supported Commands

## Game Control Commands

| Command | Parameters | Example | Status |
|---------|------------|---------|--------|
| `help` | 0 | `help` | ✅ Verified |
| `quit` | 0 | `quit` | ✅ Verified |
| `debugvictims` | 0 | `debugvictims` | ✅ Verified |
| `runrescuebot` | 0 | `runrescuebot` | ✅ Verified |

## Conditional Commands

| Command | Parameters | Example | Status |
|---------|------------|---------|--------|
| `if` | 3 | `if VictimsDead <value> <command>` | ✅ Variable verified, format confirmed |
| `ifnot` | 3 | `ifnot <varname> <value> <command>` | ⚠️ Illustrative placeholder |
| `if<=` | 3 | `if<= <varname> <value> <command>` | ⚠️ Illustrative placeholder |
| `if<` | 3 | `if< <varname> <value> <command>` | ⚠️ Illustrative placeholder |
| `if>=` | 3 | `if>= <varname> <value> <command>` | ⚠️ Illustrative placeholder |
| `if>` | 3 | `if> <varname> <value> <command>` | ⚠️ Illustrative placeholder |
| `iffacing` | 2 | `iffacing <direction> <command>` | ⚠️ Illustrative placeholder |
| `ifnotfacing` | 2 | `ifnotfacing <direction> <command>` | ⚠️ Illustrative placeholder |
| `ifclear` | 2 | `ifclear <location> <command>` | ⚠️ Illustrative placeholder |
| `ifnotclear` | 2 | `ifnotclear <location> <command>` | ⚠️ Illustrative placeholder |

## Variable Management

| Command | Parameters | Example | Status |
|---------|------------|---------|--------|
| `set` | 2 | `set BlahblahVar 42` | ✅ Variable verified from binary |
| `inc` | 1 | `inc blahCount` | ✅ Variable verified from binary |
| `dec` | 1 | `dec <varname>` | ⚠️ Illustrative placeholder |
| `listvars` | 0 | `listvars` | ✅ Verified |

## Execution Commands

| Command | Parameters | Example | Status |
|---------|------------|---------|--------|
| `exec` | 1 | `exec blah.cfg` | ✅ File verified from binary |
| `execsetsonly` | 1 | `execsetsonly <scriptname>` | ⚠️ Illustrative placeholder |
| `once` | 1 | `once <command>` | ⚠️ Illustrative placeholder |

## Communication

| Command | Parameters | Example | Status |
|---------|------------|---------|--------|
| `action` | 2 | `action <entity> <actionname>` | ⚠️ Illustrative placeholder |
| `tell` | 2 | `tell <target> <message>` | ⚠️ Illustrative placeholder |
| `sendmsg` | 2 | `sendmsg <target> <message>` | ⚠️ Illustrative placeholder |
| `print` | 1 | `print "Testing new line"` | ✅ Verified from binary |
| `hint` | 1 | `hint You must rescue` | ✅ Verified from binary |

## Audio Commands

| Command | Parameters | Example | Status |
|---------|------------|---------|--------|
| `playsnd` | 1 | `playsnd res_music01.wav` | ✅ Sound file verified from binary |
| `playsndat` | 2 | `playsndat <soundname> <location>` | ⚠️ Illustrative placeholder |
| `stopsnd` | 1 | `stopsnd <soundname>` | ⚠️ Illustrative placeholder |
| `loopsnd` | 1 | `loopsnd <soundname>` | ⚠️ Illustrative placeholder |
| `loopsndat` | 2 | `loopsndat <soundname> <location>` | ⚠️ Illustrative placeholder |
| `loopsndatloc` | 4 | `loopsndatloc <sound> <x> <y> <z>` | ⚠️ Illustrative placeholder |
| `ambientsnd` | 4 | `ambientsnd <sound> <x> <y> <z>` | ⚠️ Illustrative placeholder |
| `testloopsnd` | 1 | `testloopsnd <soundname>` | ⚠️ Illustrative placeholder |
| `testambientsnd` | 1 | `testambientsnd <soundname>` | ⚠️ Illustrative placeholder |

## Visual Effects

| Command | Parameters | Example | Status |
|---------|------------|---------|--------|
| `fogenable` | 5 | `fogenable <r> <g> <b> <density> <distance>` | ⚠️ Format verified, no example found |
| `fogdisable` | 0 | `fogdisable` | ✅ Verified |
| `quake` | 2 | `quake <intensity> <duration>` | ⚠️ Format verified, no example found |

## Map/Level Management

| Command | Parameters | Example | Status |
|---------|------------|---------|--------|
| `listmaps` | 0 | `listmaps` | ✅ Verified |
| `loadmap` | 1 | `loadmap <mapname>` | ⚠️ Illustrative placeholder |
| `loadhosemap` | 1 | `loadhosemap <mapname>` | ⚠️ Illustrative placeholder |
| `setlighttable` | 2 | `setlighttable <index> <tablename>` | ⚠️ Format verified, no example found |
| `difficulty` | 1 | `difficulty <0-2>` | ✅ Format verified (0=easy, 1=med, 2=hard) |

## Flow Control

| Command | Parameters | Example | Status |
|---------|------------|---------|--------|
| `break` | 0 | `break` | ✅ Verified |
| `ignore` | 2 | `ignore <entity> <flag>` | ⚠️ Illustrative placeholder |

---

### Legend

* **✅ Verified** - Command fully verified from binary analysis
* **⚠️ Illustrative placeholder** - Command exists but parameters are estimated/not confirmed
* **⚠️ Format verified, no example found** - Parameter format confirmed but no real-world example discovered

# Notes

Each method gave a slightly different list of cammands.

- [console_full_list.txt](console_full_list.txt) contains the combined list.

- [console_decomp.c](console_decomp.c) contains raw decompiled code containing all console variables.
