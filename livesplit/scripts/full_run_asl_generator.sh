#!/bin/bash
set -e  # Exit on error

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source the configuration file
source "$SCRIPT_DIR/config.sh"

echo "======================================"
echo "Full Run ASL Generator"
echo "======================================"
echo "Repository Root: $REPO_ROOT"
echo "Maplist File: $FULL_RUN_MAPLIST_FILE"
echo "Template File: $FULL_RUN_TEMPLATE_FILE"
echo "Output File: $FULL_RUN_OUTPUT_FILE"
echo "======================================"

# Change to repository root
cd "$REPO_ROOT"

# Verify required files exist
if [ ! -f "$FULL_RUN_MAPLIST_FILE" ]; then
    echo "ERROR: Maplist file not found: $FULL_RUN_MAPLIST_FILE"
    exit 1
fi

if [ ! -f "$FULL_RUN_TEMPLATE_FILE" ]; then
    echo "ERROR: Template file not found: $FULL_RUN_TEMPLATE_FILE"
    exit 1
fi

# Parse maplist into groups and standalone maps
echo "Parsing maplist..."
declare -A groups
declare -a group_order
declare -a standalone_maps
declare -a all_maps_order

current_group=""
current_group_prefix=""

while IFS= read -r line; do
    # Trim whitespace
    line=$(echo "$line" | tr -d '\r' | xargs)
    
    # Skip empty lines
    [ -z "$line" ] && continue
    
    # Check if it's a group marker
    if [[ "$line" =~ ^\[GROUP:(.+)\]$ ]]; then
        current_group="${BASH_REMATCH[1]}"
        current_group_prefix="${current_group}_"
        group_order+=("$current_group")
        groups["$current_group"]=""
        all_maps_order+=("[GROUP:$current_group]")
        echo "  Found group: $current_group"
    else
        # It's a map name
        # Check if this map belongs to the current group (starts with group prefix)
        if [ -n "$current_group" ] && [[ "$line" == ${current_group_prefix}* ]]; then
            # Add to current group
            if [ -z "${groups[$current_group]}" ]; then
                groups["$current_group"]="$line"
            else
                groups["$current_group"]="${groups[$current_group]} $line"
            fi
            echo "    - $line (in $current_group)"
        else
            # Standalone map (or map that doesn't match current group)
            if [ -n "$current_group" ]; then
                echo "  End of group: $current_group"
                current_group=""
                current_group_prefix=""
            fi
            standalone_maps+=("$line")
            echo "    Map: $line (standalone)"
        fi
        all_maps_order+=("$line")
    fi
done < "$FULL_RUN_MAPLIST_FILE"

echo ""
echo "Found ${#standalone_maps[@]} standalone maps"
echo "Found ${#group_order[@]} groups"

# Read template file
template_content=$(cat "$FULL_RUN_TEMPLATE_FILE")

# Note: We keep the placeholders in init block for replacement, only remove from startup collections

# Build the mapGroups dictionary
echo ""
echo "Building map groups dictionary..."
map_groups_dict=""
for group_name in "${group_order[@]}"; do
    maps_in_group="${groups[$group_name]}"
    map_list=""
    for map in $maps_in_group; do
        if [ -z "$map_list" ]; then
            map_list="\"$map\""
        else
            map_list="$map_list, \"$map\""
        fi
    done
    
    if [ -z "$map_groups_dict" ]; then
        map_groups_dict="        { \"$group_name\", new List<string> { $map_list } }"
    else
        map_groups_dict="$map_groups_dict,
        { \"$group_name\", new List<string> { $map_list } }"
    fi
done

# Build standalone maps set
echo "Building standalone maps set..."
standalone_set=""
for map in "${standalone_maps[@]}"; do
    if [ -z "$standalone_set" ]; then
        standalone_set="        \"$map\""
    else
        standalone_set="$standalone_set,
        \"$map\""
    fi
done

# Build group progress dict
echo "Building group progress dictionary..."
group_progress_dict=""
group_progress_init=""
for group_name in "${group_order[@]}"; do
    if [ -z "$group_progress_dict" ]; then
        group_progress_dict="        { \"$group_name\", 0 }"
    else
        group_progress_dict="$group_progress_dict,
        { \"$group_name\", 0 }"
    fi
    
    group_progress_init="$group_progress_init
    vars.groupProgress[\"$group_name\"] = 0;"
done

# Replace in template
output_content="$template_content"

# Replace map groups
output_content=$(echo "$output_content" | awk -v new="$map_groups_dict" '
    /vars\.mapGroups = new Dictionary/ {
        print $0
        getline
        print "    {"
        print new
        getline
        # Skip until we find the closing };
        while ($0 !~ /^    };$/) getline
        print "    };"
        next
    }
    { print }
')

# Replace standalone maps
output_content=$(echo "$output_content" | awk -v new="$standalone_set" '
    /vars\.standaloneMaps = new HashSet/ {
        print $0
        getline
        print "    {"
        print new
        getline
        # Skip until we find the closing };
        while ($0 !~ /^    };$/) getline
        print "    };"
        next
    }
    { print }
')

# Replace group progress dict
output_content=$(echo "$output_content" | awk -v new="$group_progress_dict" '
    /vars\.groupProgress = new Dictionary/ {
        print $0
        getline
        print "    {"
        print new
        getline
        # Skip until we find the closing };
        while ($0 !~ /^    };$/) getline
        print "    };"
        next
    }
    { print }
')

# Replace group progress init in init block
output_content=$(echo "$output_content" | awk -v new="$group_progress_init" '
    /\/\/ Reset flags when game loads/ {
        print $0
        getline; print $0  # vars.hasStarted
        getline; print $0  # vars.completedStandalone.Clear()
        getline; print $0  # vars.completedGroups.Clear()
        getline # blank line or first groupProgress line
        # Skip all placeholder groupProgress lines
        while ($0 ~ /vars\.groupProgress\[/) {
            getline
        }
        # Print the generated group progress lines
        print new
        print $0  # Print the line after groupProgress (vars.lastCompletedMap or blank)
        next
    }
    { print }
')

# Write output file
echo "$output_content" > "$FULL_RUN_OUTPUT_FILE"

echo ""
echo "======================================"
echo "Generation complete!"
echo "======================================"
echo "Output file: $FULL_RUN_OUTPUT_FILE"
echo "File size: $(stat -c%s "$FULL_RUN_OUTPUT_FILE" 2>/dev/null || stat -f%z "$FULL_RUN_OUTPUT_FILE") bytes"
echo ""
echo "Sample output (first 30 lines):"
head -30 "$FULL_RUN_OUTPUT_FILE"
echo ""
echo "Done!"
