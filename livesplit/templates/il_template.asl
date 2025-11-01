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
     *   Values: Level names like "{{MAP_NAME_PLACEHOLDER}}", "mission1", etc.
     *   Usage Examples:
     *     - Check specific level: current.mapName.ToLower().Contains("{{MAP_NAME_PLACEHOLDER}}")
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
    settings.Add("autostart", true, "Auto-start timer on {{MAP_NAME_PLACEHOLDER}} level");
    settings.Add("autosplit", true, "Auto-split on level end sound");
    
    // Prevent double-triggers
    vars.hasStarted = false;
    vars.hasSplit = false;
    vars.gameReady = false;
    
    print("[STARTUP] IL mode initialized");
}

init
{
    // Reset flags when game loads
    vars.hasStarted = false;
    vars.hasSplit = false;
    vars.gameReady = false;
    print("[INIT] Reset complete - hasStarted: false, hasSplit: false");
}

start
{
    // Start when: game state becomes 1 AND map is "{{MAP_NAME_PLACEHOLDER}}"
    if (settings["autostart"] && 
        current.gameState == 1 && 
        old.gameState != 1 && 
        current.mapName.ToLower().Trim().Contains("{{MAP_NAME_PLACEHOLDER}}") &&
        !vars.hasStarted)
    {
        print("[START] Timer started - map: '" + current.mapName + "'");
        vars.hasStarted = true;
        vars.hasSplit = false;
        return true;
    }
    
    if (settings["autostart"] && current.gameState == 1 && old.gameState != 1)
    {
        print("[START] Checked start - gameState changed, map: '" + current.mapName + "', hasStarted: " + vars.hasStarted);
    }
}

split
{
    if (!vars.gameReady)
        return false;
    
    if (settings["autosplit"] && 
        current.levelEndSoundPlayed != 0 && 
        old.levelEndSoundPlayed == 0 &&
        !vars.hasSplit)
    {
        print("[SPLIT] Level end sound - splitting");
        vars.hasSplit = true;
        return true;
    }
    
    if (settings["autosplit"] && current.levelEndSoundPlayed != 0 && old.levelEndSoundPlayed == 0)
    {
        print("[SPLIT] Level end sound detected but hasSplit already true");
    }
}

isLoading
{
    // Pause timer during loading screens
    // Detect loading state if gameState indicates loading
    return false;
}

update
{
    if (current.gameState == 0 && old.gameState == 0)
    {
        if (vars.gameReady)
        {
            print("[UPDATE] Returned to menu - game no longer ready");
            vars.gameReady = false;
        }
        return false;
    }
    
    if (!vars.gameReady && current.gameState == 1)
    {
        vars.gameReady = true;
        print("[UPDATE] Game ready - in level");
    }
}
