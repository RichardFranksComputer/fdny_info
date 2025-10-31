state("FDNYFirefighter", "1.0")
{
    /*
     * ==============================================================================
     * FDNY FIREFIGHTER - MEMORY VARIABLES REFERENCE
     * ==============================================================================
     * 
     * All variables below are accessible via 'current' and 'old' state objects:
     *   - current.variableName = current frame value
     *   - old.variableName = previous frame value
     * 
     * Use state comparison (current vs old) to detect changes and trigger actions.
     * 
     * ------------------------------------------------------------------------------
     * 
     * gameState (int)
     *   Address: 0x00502AAC -> 0x6F0
     *   Values:
     *     0 = Main Menu / Not in game
     *     1 = In-Game / Playing level
     *   Usage Examples:
     *     - Start timer: current.gameState == 1 && old.gameState != 1
     *     - Detect exit to menu: current.gameState == 0 && old.gameState == 1
     * 
     * mapName (string10)
     *   Address: 0x00502AAC -> 0x688 -> 0x0 -> 0xC
     *   Type: 10-character string
     *   Values: Level names like "subway_b", "mission1", etc.
     *   Usage Examples:
     *     - Check specific level: current.mapName.ToLower().Contains("subway_b")
     *     - Level change: current.mapName != old.mapName
     *     - Level-specific splits: Use in combination with other triggers
     * 
     * totalVictims (int)
     *   Address: 0x00503A78 -> 0x30 -> 0x3528
     *   Values: Number of total victims in the current level (e.g., 5, 10)
     *   Usage Examples:
     *     - Check completion: current.rescuedVictims == current.totalVictims
     *     - Verify level loaded: current.totalVictims > 0
     * 
     * rescuedVictims (int)
     *   Address: 0x00503A78 -> 0x30 -> 0x352C
     *   Values: Count of victims rescued so far (0 to totalVictims)
     *   Usage Examples:
     *     - Split on each rescue: current.rescuedVictims > old.rescuedVictims
     *     - Split on specific count: current.rescuedVictims == 3
     *     - All rescued: current.rescuedVictims == current.totalVictims
     * 
     * levelEndSoundPlayed (int)
     *   Address: 0x00503A78 -> 0x8 -> 0x0 -> 0x104 -> 0x0
     *   Values:
     *     0 = Sound has not played / Level not complete
     *     Non-zero = Level end sound has played (completion)
     *   Usage Examples:
     *     - Split on completion: current.levelEndSoundPlayed != 0 && old.levelEndSoundPlayed == 0
     */
    
    int gameState : 0x00502AAC, 0x6F0;
    string10 mapName : 0x00502AAC, 0x688, 0x0, 0xC;
    int totalVictims : 0x00503A78, 0x30, 0x3528;
    int rescuedVictims : 0x00503A78, 0x30, 0x352C;
    int levelEndSoundPlayed : 0x00503A78, 0x8, 0x0, 0x104, 0x0;
}

startup
{
    settings.Add("autostart", true, "Auto-start timer on subway_b level");
    settings.Add("autosplit", true, "Auto-split on level end sound");
    
    // Prevent double-triggers
    vars.hasStarted = false;
    vars.hasSplit = false;
}

init
{
    // Reset flags when game loads
    vars.hasStarted = false;
    vars.hasSplit = false;
}

start
{
    // Start when: game state becomes 1 AND map is "subway_b"
    if (settings["autostart"] && 
        current.gameState == 1 && 
        old.gameState != 1 && 
        current.mapName.ToLower().Contains("subway_b") &&
        !vars.hasStarted)
    {
        vars.hasStarted = true;
        vars.hasSplit = false;
        return true;
    }
}

split
{
    if (settings["autosplit"] && 
        current.levelEndSoundPlayed != 0 && 
        old.levelEndSoundPlayed == 0 &&
        !vars.hasSplit)
    {
        vars.hasSplit = true;
        return true;
    }
}

isLoading
{
    // Pause timer during loading screens
    // Detect loading state if gameState indicates loading
    return false;
}
