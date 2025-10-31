#!/bin/bash
# Configuration file for ASL generators

# Get repository root dynamically
REPO_ROOT="$(git rev-parse --show-toplevel)"

# Define directory paths
LIVESPLIT_DIR="$REPO_ROOT/livesplit"
SCRIPTS_DIR="$LIVESPLIT_DIR/scripts"
TEMPLATES_DIR="$LIVESPLIT_DIR/templates"

# Individual Level (IL) ASL paths
IL_MAPLIST_FILE="$LIVESPLIT_DIR/il_maplist.txt"
IL_TEMPLATE_FILE="$TEMPLATES_DIR/il_template.asl"
IL_FOLDER="$LIVESPLIT_DIR/individual_level_asls"

# Full Run ASL paths
FULL_RUN_MAPLIST_FILE="$LIVESPLIT_DIR/full_run_maplist.txt"
FULL_RUN_TEMPLATE_FILE="$TEMPLATES_DIR/full_run_template.asl"
FULL_RUN_NO_GROUPS_TEMPLATE_FILE="$TEMPLATES_DIR/full_run_no_groups_template.asl"
FULL_RUN_OUTPUT_FILE="$LIVESPLIT_DIR/full_run_asls/full_run.asl"
FULL_RUN_NO_GROUPS_OUTPUT_FILE="$LIVESPLIT_DIR/full_run_asls/full_run_no_groups.asl"

# Define placeholder variable names
MAP_PLACEHOLDER_VAR_NAME="{{MAP_NAME_PLACEHOLDER}}"
GROUP_PLACEHOLDER_VAR_NAME="{{GROUP_NAME_PLACEHOLDER}}"