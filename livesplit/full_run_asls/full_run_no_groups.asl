state("FDNYFirefighter", "1.0")
{
    /*
     * ==============================================================================
     * FDNY FIREFIGHTER - FULL RUN NO GROUPS AUTO SPLITTER TEMPLATE
     * ==============================================================================
     * 
     * This template is used to generate full_run_no_groups.asl with flat splits.
     * All maps can be completed in any order, no grouping enforced.
     * 
     * Memory addresses match IL template for consistency.
     */
    
    int gameState : 0x00502AAC, 0x6F0;
    string10 mapName : 0x00502AAC, 0x688, 0x0, 0xC;
    int totalVictims : 0x00503A78, 0x30, 0x3528;
    int rescuedVictims : 0x00503A78, 0x30, 0x352C;
    int levelEndSoundPlayed : 0x00503A78, 0x8, 0x0, 0x104, 0x0;
}

startup
{
    settings.Add("autostart", true, "Auto-start timer");

    // All maps that need to be completed (any order)
    vars.allMaps = new HashSet<string>
    {
        "bank",
        "bar_r",
        "boat_a",
        "boat_b",
        "gas_r",
        "mbase",
        "oil_rig_a",
        "oil_rig_b",
        "oil_rig_c",
        "oil_rig_d",
        "subway_a",
        "subway_b",
        "training"
    };
    
    // Track completed maps
    vars.completedMaps = new HashSet<string>();
    
    // Prevent double-triggers
    vars.lastCompletedMap = "";
    vars.gameReady = false;
    vars.hasStarted = false;
    
    print("[STARTUP] Tracking " + vars.allMaps.Count + " maps");
}

init
{
    // Reset flags when game loads
    vars.completedMaps.Clear();
    vars.lastCompletedMap = "";
    vars.gameReady = false;
    vars.hasStarted = false;
    print("[INIT] Reset complete - completedMaps cleared, lastCompletedMap cleared");
}

start
{
    // Start when: game state becomes 1
    if (settings["autostart"] && 
        current.gameState == 1 && 
        old.gameState != 1 && 
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
    
    // Split when level end sound plays (map completion)
    if (current.levelEndSoundPlayed != 0 && 
        old.levelEndSoundPlayed == 0)
    {
        print("[SOUND] Level end sound detected - raw mapName: '" + current.mapName + "'");
        string completedMap = current.mapName.ToLower().Trim();
        print("[MAP] Processed map: '" + completedMap + "'");
        
        // Check if this map needs to be tracked
        if (vars.allMaps.Contains(completedMap) && 
            !vars.completedMaps.Contains(completedMap))
        {
            // Prevent duplicate splits for same map
            if (completedMap == vars.lastCompletedMap)
            {
                print("[DUPLICATE] Blocked duplicate split for: " + completedMap);
                return false;
            }
            
            vars.lastCompletedMap = completedMap;
            vars.completedMaps.Add(completedMap);
            print("Completed: " + completedMap + " (" + vars.completedMaps.Count + "/" + vars.allMaps.Count + ")");
            return true;
        }
        else if (!vars.allMaps.Contains(completedMap))
        {
            print("[MAP] Not tracked: " + completedMap);
        }
        else
        {
            print("[MAP] Already completed: " + completedMap);
        }
    }
    
    return false;
}

reset
{
    // Manual reset only - no auto-reset
    return false;
}

isLoading
{
    // No load time removal
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
    
    if (current.gameState == 0 && old.gameState != 0)
    {
        print("[UPDATE] Exited to menu - resetting hasStarted");
        vars.hasStarted = false;
        vars.gameReady = false;
    }
    
    if (!vars.gameReady && current.gameState == 1)
    {
        vars.gameReady = true;
        print("[UPDATE] Game ready - in level");
    }
}
