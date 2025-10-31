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
}

init
{
    // Reset flags when game loads
    vars.completedMaps.Clear();
    vars.lastCompletedMap = "";
}

start
{
    // Manual start only - no auto-start
    return false;
}

split
{
    // Split when level end sound plays (map completion)
    if (current.levelEndSoundPlayed != 0 && 
        old.levelEndSoundPlayed == 0)
    {
        string completedMap = current.mapName.ToLower();
        
        // Prevent duplicate splits for same map
        if (completedMap == vars.lastCompletedMap)
            return false;
        
        vars.lastCompletedMap = completedMap;
        
        // Check if this map needs to be tracked
        if (vars.allMaps.Contains(completedMap) && 
            !vars.completedMaps.Contains(completedMap))
        {
            vars.completedMaps.Add(completedMap);
            print("Completed: " + completedMap + " (" + vars.completedMaps.Count + "/" + vars.allMaps.Count + ")");
            return true;
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
    // Display current progress for debugging
    if (current.mapName != old.mapName)
    {
        print("Map changed to: " + current.mapName);
    }
}
