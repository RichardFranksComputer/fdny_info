# Console commands

Commands were found via:
    - `strings FDNYFIREFIGHTER.exe | grep -C 50 -i playsnd`
    - decompiling .exe in Ghidra and searching `playsnd`

# Supported Commands

## Game Control Commands
* `help` - Display help
* `quit` - Exit game
* `debugvictims` - Debug victim entities
* `runrescuebot` - Run rescue bot AI

## Conditional Commands
* `if` - Conditional execution with 3 parameters
* `ifnot` - Inverse conditional
* `if<=`, `if<`, `if>=`, `if>` - Numeric comparisons
* `iffacing` - Check facing direction
* `ifnotfacing` - Inverse facing check
* `ifclear` - Check if area is clear
* `ifnotclear` - Inverse clear check

## Variable Management
* `set` - Set variable value (2 parameters)
* `inc` - Increment variable
* `dec` - Decrement variable
* `listvars` - List all variables

## Execution Commands
* `exec` - Execute script
* `execsetsonly` - Execute only set commands
* `once` - Execute once

## Communication
* `action` - Perform action (2 parameters)
* `tell` - Send message (2 parameters)
* `sendmsg` - Send message (2 parameters)
* `print` - Print message
* `hint` - Display hint

## Audio Commands
* `playsnd` - Play sound
* `playsndat` - Play sound at location (2 parameters)
* `stopsnd` - Stop sound
* `loopsnd` - Loop sound
* `loopsndat` - Loop sound at location (2 parameters)
* `loopsndatloc` - Loop sound at specific location (4 parameters)
* `ambientsnd` - Ambient sound (4 parameters)
* `testloopsnd` - Test looping sound
* `testambientsnd` - Test ambient sound

## Visual Effects
* `fogenable` - Enable fog (5 parameters: likely RGBA + distance)
* `fogdisable` - Disable fog
* `quake` - Screen shake effect (2 parameters: intensity + duration)

## Map/Level Management
* `listmaps` - List available maps
* `loadmap` - Load specific map
* `loadhosemap` - Load HOS (possibly "House of Sorrow" or similar) map
* `setlighttable` - Set lighting table (2 parameters)
* `difficulty` - Set difficulty level

## Flow Control
* `break` - Break from loop
* `ignore` - Ignore certain conditions (2 parameters)

# Notes

Each method gave a slightly different list of cammands. [console_full_list.txt](console_full_list.txt) contains the combined list.

- [console_decomp.c](console_decomp.c) contains raw decompiled code containing all console variables.
- [console_decomp_list.txt](console_decomp_list.txt] contains variables extracted from the conosle
- [console_exe_strings_list.txt](console_exe_strings_list.txt) contains variables extracted from `strings` command