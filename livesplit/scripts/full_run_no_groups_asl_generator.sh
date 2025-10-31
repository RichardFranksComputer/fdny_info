#!/bin/bash
set -e  # Exit on error

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source the configuration file
source "$SCRIPT_DIR/config.sh"

echo "======================================"
echo "Full Run No Groups ASL Generator"
echo "======================================"
echo "Repository Root: $REPO_ROOT"
echo "Maplist File: $FULL_RUN_MAPLIST_FILE"
echo "Template File: $FULL_RUN_NO_GROUPS_TEMPLATE_FILE"
echo "Output File: $FULL_RUN_NO_GROUPS_OUTPUT_FILE"
echo "======================================"

# Change to repository root
cd "$REPO_ROOT"

# Verify required files exist
if [ ! -f "$FULL_RUN_MAPLIST_FILE" ]; then
    echo "ERROR: Maplist file not found: $FULL_RUN_MAPLIST_FILE"
    exit 1
fi

if [ ! -f "$FULL_RUN_NO_GROUPS_TEMPLATE_FILE" ]; then
    echo "ERROR: Template file not found: $FULL_RUN_NO_GROUPS_TEMPLATE_FILE"
    exit 1
fi

# Parse all maps from maplist (ignore group markers)
echo "Parsing maplist..."
declare -a all_maps

while IFS= read -r line; do
    # Trim whitespace
    line=$(echo "$line" | tr -d '\r' | xargs)
    
    # Skip empty lines and group markers
    [ -z "$line" ] && continue
    [[ "$line" =~ ^\[GROUP: ]] && continue
    
    # It's a map name
    all_maps+=("$line")
    echo "  - $line"
done < "$FULL_RUN_MAPLIST_FILE"

echo ""
echo "Found ${#all_maps[@]} maps total"

# Read template file
template_content=$(cat "$FULL_RUN_NO_GROUPS_TEMPLATE_FILE")

# Remove template placeholder lines
template_content=$(echo "$template_content" | grep -v "$MAP_PLACEHOLDER_VAR_NAME")

# Build all maps set
echo "Building all maps set..."
all_maps_set=""
for map in "${all_maps[@]}"; do
    if [ -z "$all_maps_set" ]; then
        all_maps_set="        \"$map\""
    else
        all_maps_set="$all_maps_set,
        \"$map\""
    fi
done

# Replace in template
output_content="$template_content"

# Replace all maps set
output_content=$(echo "$output_content" | awk -v new="$all_maps_set" '
    /vars\.allMaps = new HashSet/ {
        print $0
        getline
        print "    {"
        print new
        getline
        while ($0 !~ /};/) getline
        print "    };"
        next
    }
    { print }
')

# Write output file
echo "$output_content" > "$FULL_RUN_NO_GROUPS_OUTPUT_FILE"

echo ""
echo "======================================"
echo "Generation complete!"
echo "======================================"
echo "Output file: $FULL_RUN_NO_GROUPS_OUTPUT_FILE"
echo "File size: $(stat -c%s "$FULL_RUN_NO_GROUPS_OUTPUT_FILE" 2>/dev/null || stat -f%z "$FULL_RUN_NO_GROUPS_OUTPUT_FILE") bytes"
echo ""
echo "Sample output (first 30 lines):"
head -30 "$FULL_RUN_NO_GROUPS_OUTPUT_FILE"
echo ""
echo "Done!"
