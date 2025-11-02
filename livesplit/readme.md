# LiveSplit Auto Splitters for FDNY Firefighter

Automated ASL file generation for FDNY Firefighter speedruns.

I have no idea how to use LiveSplit or if the way I'm doing this is functional.  This will be updated as I continue.

## Quick Start - Editing in GitHub

**To add/modify maps or change split behavior:**

1. Fork this repo, and perform the following steps in the forked repo
2. Edit files directly in GitHub (click pencil icon)
3. Commit changes
4. ASL files automatically regenerate via GitHub Actions

**Edit these files:**
- `il_maplist.txt` - Add/remove individual level maps (one per line)
- `full_run_maplist.txt` - Add/remove maps, modify groupings with `[GROUP:name]` markers
- `templates/*.asl` - Modify ASL logic (use `{{MAP_NAME_PLACEHOLDER}}` and `{{GROUP_NAME_PLACEHOLDER}}`)

## Generators

**Individual Level (IL):** `templates/il_template.asl` → 13 individual ASL files (one per map)

**Full Run (Groups):** `templates/full_run_template.asl` → `full_run.asl` (groups enforce in-order completion)

**Full Run (No Groups):** `templates/full_run_no_groups_template.asl` → `full_run_no_groups.asl` (any order)

## Usage

```bash
./livesplit/scripts/il_asl_generator.sh              # Generate IL ASLs
./livesplit/scripts/full_run_asl_generator.sh        # Generate full run (groups)
./livesplit/scripts/full_run_no_groups_asl_generator.sh  # Generate full run (flat)
```

## Maplist Formats

**`il_maplist.txt`** - One map per line

**`full_run_maplist.txt`** - Group markers for sequencing:
```
bank
[GROUP:boat]
boat_a
boat_b
[GROUP:oil_rig]
...
```
Groups require `name_` prefix. Group ends when prefix doesn't match.

## Split Behavior

**IL:** Auto-start and auto-split on level completion per map

**Full Run (Groups):**
- Standalone maps: any order
- Grouped maps: exact order (e.g., `oil_rig_a` before `oil_rig_b`)
- Out-of-order maps ignored
- Manual start/reset

**Full Run (No Groups):** All 13 maps, any order, manual start/reset

All use `levelEndSoundPlayed` for timing.

## Memory Addresses

Load `all_values_for_livesplit.ct` into Cheat Engine to verify.

- `gameState`: `0x00502AAC, 0x6F0`
- `mapName`: `0x00502AAC, 0x688, 0x0, 0xC`
- `levelEndSoundPlayed`: `0x00503A78, 0x8, 0x0, 0x104, 0x0` (sound channel, 0 until level ends)

See [find_sound_pointer.md](find_sound_pointer.md) for finding other sound pointers.