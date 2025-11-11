# LiveSplit Auto Splitters for FDNY Firefighter

## Split Behavior

### Split when:

**Single-stage maps:**
- Map is x and corresponding levelEndSound != 0

**Intermediary staged maps:**
- Last map was map_a, current map is map_b

**Final stage of staged map:**
- Same as single-stage maps

## Reset Behavior

- `FDNY_ILs.asl` autoresets when player enters menu
- `FDNY_rescue%.asl` does not autoreset under any condition