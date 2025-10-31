#!/bin/bash
set -e  # Exit on error

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source the configuration file
source "$SCRIPT_DIR/config.sh"

echo "======================================"
echo "IL ASL Generator"
echo "======================================"
echo "Repository Root: $REPO_ROOT"
echo "Livesplit Directory: $LIVESPLIT_DIR"
echo "Maplist File: $IL_MAPLIST_FILE"
echo "Template File: $IL_TEMPLATE_FILE"
echo "Output Folder: $IL_FOLDER"
echo "Placeholder: $MAP_PLACEHOLDER_VAR_NAME"
echo "======================================"

# Change to repository root
cd "$REPO_ROOT"

# Verify required files exist
if [ ! -f "$IL_MAPLIST_FILE" ]; then
    echo "ERROR: Maplist file not found: $IL_MAPLIST_FILE"
    exit 1
fi

if [ ! -f "$IL_TEMPLATE_FILE" ]; then
    echo "ERROR: Template file not found: $IL_TEMPLATE_FILE"
    exit 1
fi

# Ensure output folder exists
mkdir -p "$IL_FOLDER"

# Clear existing files in output folder
echo "Cleaning output folder..."
rm -f "$IL_FOLDER"/*.asl

# Read maps into array
echo "Reading maps from $IL_MAPLIST_FILE..."
maparray=()
while IFS= read -r line; do
    # Trim whitespace and skip empty lines
    line=$(echo "$line" | tr -d '\r' | xargs)
    if [ -n "$line" ]; then
        maparray+=("$line")
    fi
done < "$IL_MAPLIST_FILE"

echo "Found ${#maparray[@]} maps to process"

# Generate ASL files
echo "Generating ASL files..."
for map in "${maparray[@]}"; do
    output_file="$IL_FOLDER/${map}.asl"
    echo "  - Creating $map.asl..."
    
    # Replace placeholder with map name
    sed "s/$MAP_PLACEHOLDER_VAR_NAME/$map/g" "$IL_TEMPLATE_FILE" > "$output_file"
done

echo "======================================"
echo "Generation complete!"
echo "======================================"

# List generated files
echo "Files in $IL_FOLDER:"
ls -lh "$IL_FOLDER"

echo ""
echo "File count check:"
file_count=$(ls -1 "$IL_FOLDER"/*.asl 2>/dev/null | wc -l)
echo "Generated $file_count ASL files"

# Verify files are not empty
echo ""
echo "Verifying file sizes..."
for asl_file in "$IL_FOLDER"/*.asl; do
    if [ -f "$asl_file" ]; then
        size=$(stat -c%s "$asl_file" 2>/dev/null || stat -f%z "$asl_file" 2>/dev/null)
        filename=$(basename "$asl_file")
        if [ "$size" -eq 0 ]; then
            echo "  WARNING: $filename is empty!"
        else
            echo "  ✓ $filename ($size bytes)"
        fi
    fi
done

echo ""
echo "Sample content from first generated file:"
first_file=$(ls "$IL_FOLDER"/*.asl 2>/dev/null | head -1)
if [ -f "$first_file" ]; then
    echo "--- $(basename "$first_file") (first 10 lines) ---"
    head -10 "$first_file"
fi

echo ""
echo "Done!"
