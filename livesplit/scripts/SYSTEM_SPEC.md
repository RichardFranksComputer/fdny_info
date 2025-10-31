# ASL Generator System Specification
# ================================================================================
# This file defines the complete ASL generation system for FDNY Firefighter.
# Edit this file to make changes to the system, then feed it back to an AI assistant.
# ================================================================================

# SYSTEM OVERVIEW
# ================================================================================
Purpose: Automatically generate LiveSplit ASL files for FDNY Firefighter speedruns
Architecture: Template-based generation with GitHub Actions automation
Language: Bash shell scripts
Repository Root: fdny_info copy/

# FOLDER STRUCTURE
# ================================================================================
livesplit/
├── scripts/                             # Generator scripts (all bash)
│   ├── config.sh                        # Centralized configuration
│   ├── il_asl_generator.sh             # Individual Level generator
│   ├── full_run_asl_generator.sh       # Full Run (groups) generator
│   ├── full_run_no_groups_asl_generator.sh  # Full Run (flat) generator
│   └── SYSTEM_SPEC.md                  # This file
├── templates/                           # ASL templates with placeholders
│   ├── il_template.asl                 # Individual level template
│   ├── full_run_template.asl           # Full run with groups template
│   └── full_run_no_groups_template.asl # Full run flat template
├── individual_level_asls/               # Generated IL ASLs (13 files)
│   └── *.asl                           # Auto-generated, do not edit manually
├── full_run_asls/                       # Generated full run ASLs
│   ├── full_run.asl                    # Generated full run with groups
│   └── full_run_no_groups.asl          # Generated full run flat
├── il_maplist.txt                      # IL map list (plain text, one per line)
├── full_run_maplist.txt                # Full run map list (with [GROUP:name] markers)
└── readme.md                           # User documentation

.github/workflows/
├── generate-il-asls.yml                # GitHub Action for IL generation
└── generate-full-run-asls.yml          # GitHub Action for full run generation

# CONFIGURATION (config.sh)
# ================================================================================
# Dynamic Variables:
REPO_ROOT                               # Auto-detected via git rev-parse
LIVESPLIT_DIR                          # $REPO_ROOT/livesplit
SCRIPTS_DIR                            # $LIVESPLIT_DIR/scripts
TEMPLATES_DIR                          # $LIVESPLIT_DIR/templates

# Individual Level Paths:
IL_MAPLIST_FILE                        # $LIVESPLIT_DIR/il_maplist.txt
IL_TEMPLATE_FILE                       # $TEMPLATES_DIR/il_template.asl
IL_FOLDER                              # $LIVESPLIT_DIR/individual_level_asls

# Full Run Paths:
FULL_RUN_MAPLIST_FILE                  # $LIVESPLIT_DIR/full_run_maplist.txt
FULL_RUN_TEMPLATE_FILE                 # $TEMPLATES_DIR/full_run_template.asl
FULL_RUN_NO_GROUPS_TEMPLATE_FILE       # $TEMPLATES_DIR/full_run_no_groups_template.asl
FULL_RUN_OUTPUT_FILE                   # $LIVESPLIT_DIR/full_run_asls/full_run.asl
FULL_RUN_NO_GROUPS_OUTPUT_FILE         # $LIVESPLIT_DIR/full_run_asls/full_run_no_groups.asl

# Placeholder Variables:
MAP_PLACEHOLDER_VAR_NAME               # "{{MAP_NAME_PLACEHOLDER}}"
GROUP_PLACEHOLDER_VAR_NAME             # "{{GROUP_NAME_PLACEHOLDER}}"

# Usage in Scripts:
# All generator scripts source config.sh to access these variables
# GitHub Actions workflows also source config.sh directly for path references

# GENERATOR SCRIPTS
# ================================================================================

# 1. IL ASL Generator (il_asl_generator.sh)
# --------------------------------------------------------------------------------
Input: il_maplist.txt, il_template.asl
Output: individual_level_asls/*.asl (one file per map)
Logic:
  1. Read each map name from il_maplist.txt (one per line)
  2. For each map:
     - Copy il_template.asl
     - Replace all instances of {{MAP_NAME_PLACEHOLDER}} with map name
     - Save as individual_level_asls/{mapname}.asl
  3. Verify all files generated successfully
Process: Simple text substitution using sed

# 2. Full Run ASL Generator (full_run_asl_generator.sh)
# --------------------------------------------------------------------------------
Input: full_run_maplist.txt, full_run_template.asl
Output: full_run.asl
Logic:
  1. Parse full_run_maplist.txt:
     - Detect [GROUP:name] markers
     - Maps following marker with name_ prefix belong to that group
     - Group ends when prefix doesn't match or next [GROUP:] found
     - Other maps are standalone (any order)
  2. Build data structures:
     - Map groups dictionary: { "group_name": ["map1", "map2", ...] }
     - Standalone maps set: ["map1", "map2", ...]
     - Group progress dictionary: { "group_name": 0 }
  3. Replace template sections using awk:
     - vars.mapGroups = ... (replace entire Dictionary block)
     - vars.standaloneMaps = ... (replace entire HashSet block)
     - vars.groupProgress = ... (replace entire Dictionary block)
     - init block: Find placeholder groupProgress lines, skip all, insert generated ones
  4. Template placeholders remain until awk replacement (not pre-removed)
  5. Write to full_run.asl
Process: Bash parsing + awk text replacement with targeted section replacement

# 3. Full Run No Groups Generator (full_run_no_groups_asl_generator.sh)
# --------------------------------------------------------------------------------
Input: full_run_maplist.txt, full_run_no_groups_template.asl
Output: full_run_no_groups.asl
Logic:
  1. Parse full_run_maplist.txt:
     - Read all map names
     - Ignore [GROUP:] markers
  2. Build data structure:
     - All maps set: ["map1", "map2", ...]
  3. Replace template section:
     - vars.allMaps = ... (generated from all maps)
  4. Remove template placeholder lines
  5. Write to full_run_no_groups.asl
Process: Bash parsing + awk text replacement

# MAPLIST FORMATS
# ================================================================================

# il_maplist.txt Format:
# --------------------------------------------------------------------------------
# Plain text, one map name per line
# No special markers
# Example:
#   bank
#   bar_r
#   boat_a
#   ...

# full_run_maplist.txt Format:
# --------------------------------------------------------------------------------
# Plain text with group markers
# Format:
#   standalone_map1
#   standalone_map2
#   [GROUP:group_name]
#   group_name_map1
#   group_name_map2
#   standalone_map3
#   [GROUP:another_group]
#   another_group_map1
#   ...
#
# Rules:
#   - [GROUP:name] starts a group
#   - Following maps with name_ prefix belong to that group
#   - Group ends when a map doesn't have the prefix
#   - Maps outside groups are standalone (any order)
#   - Groups enforce sequential completion within the group

# TEMPLATE FILES
# ================================================================================

# Template Placeholders:
{{MAP_NAME_PLACEHOLDER}}               # Replaced with actual map names
{{GROUP_NAME_PLACEHOLDER}}             # Replaced with actual group names

# Template Structure (all templates):
# --------------------------------------------------------------------------------
state("FDNYFirefighter", "1.0") {
    # Memory addresses (consistent across all ASLs)
    int gameState : 0x00502AAC, 0x6F0;
    string10 mapName : 0x00502AAC, 0x688, 0x0, 0xC;
    int totalVictims : 0x00503A78, 0x30, 0x3528;
    int rescuedVictims : 0x00503A78, 0x30, 0x352C;
    int levelEndSoundPlayed : 0x00503A78, 0x8, 0x0, 0x104, 0x0;
}

startup { # Settings and variable initialization }
init { # Reset when game loads }
start { # Timer start logic }
split { # Split detection logic }
reset { # Manual reset only (returns false) }
isLoading { # No load removal (returns false) }
update { # Debug output }

# IL Template Specifics:
# --------------------------------------------------------------------------------
Behavior:
  - Auto-start when entering {{MAP_NAME_PLACEHOLDER}} map
  - Auto-split on levelEndSoundPlayed trigger
  - Manual reset only
  - Double-trigger prevention

# Full Run Template Specifics:
# --------------------------------------------------------------------------------
Behavior:
  - Manual start only
  - Groups enforce in-order completion
  - Standalone maps can be completed in any order
  - Out-of-order grouped maps are ignored
  - Splits on levelEndSoundPlayed trigger
  - Manual reset only

Variables to Generate:
  - vars.mapGroups (Dictionary<string, List<string>>)
  - vars.standaloneMaps (HashSet<string>)
  - vars.groupProgress (Dictionary<string, int>)
  - vars.completedGroups (HashSet<string>)
  - vars.completedStandalone (HashSet<string>)

# Full Run No Groups Template Specifics:
# --------------------------------------------------------------------------------
Behavior:
  - Manual start only
  - All maps can be completed in any order
  - No grouping or ordering enforced
  - Splits on levelEndSoundPlayed trigger
  - Manual reset only

Variables to Generate:
  - vars.allMaps (HashSet<string>)
  - vars.completedMaps (HashSet<string>)

# GITHUB ACTIONS
# ================================================================================

# generate-il-asls.yml
# --------------------------------------------------------------------------------
Triggers:
  - Push to main branch
  - Paths: livesplit/templates/il_template.asl
          livesplit/il_maplist.txt
          livesplit/scripts/il_asl_generator.sh
          livesplit/scripts/config.sh
  - Manual workflow_dispatch

Jobs:
  1. Checkout repository (fetch-depth: 0)
  2. Run il_asl_generator.sh (chmod + execute)
  3. Verify files generated (sources config.sh for $IL_FOLDER)
  4. Commit and push (sources config.sh for paths)
  5. Message: "Auto-generate individual level ASL files [skip ci]"

Path Resolution:
  - Workflows source config.sh directly using `source livesplit/scripts/config.sh`
  - Access variables like $IL_FOLDER, $FULL_RUN_OUTPUT_FILE directly
  - Single source of truth in config.sh, no duplication

# generate-full-run-asls.yml
# --------------------------------------------------------------------------------
Triggers:
  - Push to main branch
  - Paths: livesplit/templates/full_run_template.asl
          livesplit/templates/full_run_no_groups_template.asl
          livesplit/full_run_maplist.txt
          livesplit/scripts/full_run_asl_generator.sh
          livesplit/scripts/full_run_no_groups_asl_generator.sh
          livesplit/scripts/config.sh
  - Manual workflow_dispatch

Jobs:
  1. Checkout repository (fetch-depth: 0)
  2. Run both generators (chmod + execute)
  3. Verify files generated (sources config.sh for paths)
  4. Commit and push (sources config.sh for paths)
  5. Message: "Auto-generate full run ASL files [skip ci]"

Path Resolution:
  - Workflows source config.sh directly using `source livesplit/scripts/config.sh`
  - Access variables like $FULL_RUN_OUTPUT_FILE, $FULL_RUN_NO_GROUPS_OUTPUT_FILE
  - Single source of truth in config.sh, no duplication

# SPLIT BEHAVIOR LOGIC
# ================================================================================

# Individual Level (IL):
# --------------------------------------------------------------------------------
Start Condition: gameState == 1 && old.gameState != 1 && map matches template
Split Condition: levelEndSoundPlayed != 0 && old.levelEndSoundPlayed == 0
Reset: Manual only (returns false)
Timing: Real time with levelEndSoundPlayed trigger

# Full Run (With Groups):
# --------------------------------------------------------------------------------
Start Condition: Manual only (returns false)
Split Conditions:
  - Standalone map completed: Add to completedStandalone, split
  - Grouped map completed IN ORDER: Increment groupProgress, split
  - Grouped map completed OUT OF ORDER: Ignore, no split
  - Group completed: Mark in completedGroups, already split on last map
Reset: Manual only (returns false)
Timing: Real time with levelEndSoundPlayed trigger

Group Order Enforcement:
  - Track current progress index for each group
  - Only split if completed map == maps[currentProgress]
  - Ignore map if it's in the group but not the next expected map

# Full Run (No Groups):
# --------------------------------------------------------------------------------
Start Condition: Manual only (returns false)
Split Condition: Any map completed that hasn't been completed yet
Reset: Manual only (returns false)
Timing: Real time with levelEndSoundPlayed trigger

# CURRENT MAP CONFIGURATION
# ================================================================================

Total Maps: 13

All Maps:
  - bank
  - bar_r
  - boat_a
  - boat_b
  - gas_r
  - mbase
  - oil_rig_a
  - oil_rig_b
  - oil_rig_c
  - oil_rig_d
  - subway_a
  - subway_b
  - training

Groups (3):
  - boat: [boat_a, boat_b] (2 maps)
  - oil_rig: [oil_rig_a, oil_rig_b, oil_rig_c, oil_rig_d] (4 maps)
  - subway: [subway_a, subway_b] (2 maps)

Standalone (5):
  - bank
  - bar_r
  - gas_r
  - mbase
  - training

# MEMORY ADDRESSES
# ================================================================================
# All addresses are for FDNYFirefighter.exe v1.0

gameState:
  Address: 0x00502AAC, 0x6F0
  Type: int
  Values: 0 = Menu, 1 = In-Game

mapName:
  Address: 0x00502AAC, 0x688, 0x0, 0xC
  Type: string10
  Values: Map names like "training", "bank", etc.

totalVictims:
  Address: 0x00503A78, 0x30, 0x3528
  Type: int
  Values: Total victims in level

rescuedVictims:
  Address: 0x00503A78, 0x30, 0x352C
  Type: int
  Values: Current rescued count

levelEndSoundPlayed:
  Address: 0x00503A78, 0x8, 0x0, 0x104, 0x0
  Type: int
  Values: 0 = Not played, Non-zero = Level complete
  Note: Sound channel that triggers on level completion (rescue levels only)

# TESTING
# ================================================================================

# Manual Testing:
cd "/path/to/fdny_info copy"
./livesplit/scripts/il_asl_generator.sh
./livesplit/scripts/full_run_asl_generator.sh
./livesplit/scripts/full_run_no_groups_asl_generator.sh

# Expected Output:
- 13 files in livesplit/individual_level_asls/
- livesplit/full_run.asl (~4.8KB)
- livesplit/full_run_no_groups.asl (~2.6KB)

# Verification:
ls -lh livesplit/individual_level_asls/*.asl | wc -l  # Should be 13
stat livesplit/full_run.asl                            # Should exist
stat livesplit/full_run_no_groups.asl                  # Should exist
grep -c "boat" livesplit/full_run.asl                  # Should find group references

# MODIFICATION GUIDE
# ================================================================================

To Add a New Map:
1. Add map name to il_maplist.txt
2. Add map name to full_run_maplist.txt (with [GROUP:] if needed)
3. Commit changes
4. GitHub Actions will regenerate all ASLs

To Add a New Group:
1. Edit full_run_maplist.txt
2. Add [GROUP:groupname]
3. Add maps with groupname_ prefix below it
4. Commit changes
5. GitHub Actions will regenerate full run ASLs

To Modify Split Logic:
1. Edit appropriate template in livesplit/templates/
2. Keep placeholder variables intact ({{MAP_NAME_PLACEHOLDER}}, {{GROUP_NAME_PLACEHOLDER}})
3. For init block in full_run_template.asl, use single placeholder line:
   vars.groupProgress["{{GROUP_NAME_PLACEHOLDER}}"] = 0;
4. Commit changes
5. GitHub Actions will regenerate ASLs

To Change Memory Addresses:
1. Edit all three templates in livesplit/templates/
2. Update state descriptor section
3. Commit changes
4. GitHub Actions will regenerate all ASLs

To Modify Generator Logic:
1. Edit appropriate script in livesplit/scripts/
2. For full_run_asl_generator.sh: awk scripts use targeted section replacement
3. Placeholders in collections (startup) are replaced by awk, not pre-removed
4. Test locally first
5. Commit changes
6. GitHub Actions will use new logic on next trigger

# KNOWN LIMITATIONS
# ================================================================================

1. levelEndSoundPlayed only works for rescue levels
2. Group detection requires maps to have group_ prefix
3. No support for nested groups
4. Manual start/reset required for full run modes
5. No support for game time (uses real time)
6. No load time removal implemented
7. Full run template init block must use single placeholder line to avoid duplicates

# BUGFIXES APPLIED
# ================================================================================

Issue: Duplicate groupProgress variable initialization in full_run.asl
Cause: Generator script removed ALL placeholder lines at start, then awk had nothing to replace
Fix: 
  - Changed template to only use placeholder in init block
  - Modified generator to keep placeholders until awk replacement
  - Updated awk script to properly skip and replace groupProgress lines
Date: 2025-10-31

Issue: Hardcoded paths duplicated between config.sh and GitHub Actions workflows
Cause: Workflows contained literal path strings instead of sourcing from config
Fix:
  - Workflows now source config.sh directly with `source livesplit/scripts/config.sh`
  - All path references use bash variables from config ($IL_FOLDER, $FULL_RUN_OUTPUT_FILE, etc.)
  - Removed unnecessary get_paths.sh helper script that re-duplicated definitions
Benefits: True single source of truth for all paths, simpler maintenance, no intermediate scripts
Date: 2025-10-31

# FUTURE ENHANCEMENTS (POTENTIAL)
# ================================================================================

1. Support for non-rescue level detection
2. More flexible group syntax (explicit end markers)
3. Configurable start/reset behavior
4. Game time support
5. Load time removal
6. Multiple game versions support
7. Settings GUI for split customization
8. Nested group support
9. Split name customization

# END OF SPECIFICATION
# ================================================================================
