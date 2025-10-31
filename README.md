# FDNY: American Fist Fighter

A central location for the FELLAS to store technical info about FDNY.

put up a pr if you want to contribute ok

## LiveSplit Auto Splitters

The `livesplit/` folder contains automated ASL generation for FDNY Firefighter speedruns.

**Quick Start:**
```bash
./livesplit/scripts/il_asl_generator.sh              # Generate 13 individual level ASLs
./livesplit/scripts/full_run_asl_generator.sh        # Generate full run ASL (with groups)
./livesplit/scripts/full_run_no_groups_asl_generator.sh  # Generate full run ASL (flat)
```

**Key Files:**
- [livesplit/readme.md](livesplit/readme.md) - Complete LiveSplit documentation
- [livesplit/all_values_for_livesplit.ct](livesplit/all_values_for_livesplit.ct) - Cheat Engine verification file
- [livesplit/templates/](livesplit/templates/) - ASL template files
- [livesplit/individual_level_asls/](livesplit/individual_level_asls/) - Generated IL ASLs (13 files)
- [livesplit/full_run.asl](livesplit/full_run.asl) - Generated full run with groups
- [livesplit/full_run_no_groups.asl](livesplit/full_run_no_groups.asl) - Generated full run (any order)

**Features:**
- Automated generation from templates
- GitHub Actions integration
- Group-based sequencing for full runs
- Consistent memory addresses across all ASLs

## Other Info

- `console/` - Info about the console and its commands
- `rescuebot/` - Info about the rescuebot AI behavior
- `museum/` - Research notes and reverse engineering findings
- `victory_screen/` - Victory screen detection research
