state("FDNYFirefighter", "1.0")
{
    /*
     * ==============================================================================
     * FDNY FIREFIGHTER - FULL RUN AUTO SPLITTER TEMPLATE
     * ==============================================================================
     * 
     * This template is used to generate full_run.asl with grouped splits.
     * Groups require in-order completion, standalone maps can be any order.
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
    // Define map groups that must be completed in sequence within each group
    vars.mapGroups = new Dictionary<string, List<string>>
    {
        { "boat", new List<string> { "boat_a", "boat_b" } },
        { "oil_rig", new List<string> { "oil_rig_a", "oil_rig_b", "oil_rig_c", "oil_rig_d" } },
        { "subway", new List<string> { "subway_a", "subway_b" } }
    };
    
    // Standalone maps (any order)
    vars.standaloneMaps = new HashSet<string>
    {
        "bank",
        "bar_r",
        "gas_r",
        "mbase",
        "training"
    };
    
    // Track completed standalone maps
    vars.completedStandalone = new HashSet<string>();
    
    // Track progress within each group
    vars.groupProgress = new Dictionary<string, int>
    {
        { "boat", 0 },
        { "oil_rig", 0 },
        { "subway", 0 }
    };
    
    // Track which groups are complete
    vars.completedGroups = new HashSet<string>();
    
    // Prevent double-triggers
    vars.hasStarted = false;
    vars.lastCompletedMap = "";
    
    print("[STARTUP] Tracking " + vars.mapGroups.Count + " groups, " + vars.standaloneMaps.Count + " standalone maps");
}

init
{
    // Reset flags when game loads
    vars.hasStarted = false;
    vars.completedStandalone.Clear();
    vars.completedGroups.Clear();

    vars.groupProgress["boat"] = 0;
    vars.groupProgress["oil_rig"] = 0;
    vars.groupProgress["subway"] = 0;
    vars.lastCompletedMap = "";
    print("[INIT] Reset complete - all tracking cleared");
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
    // Split when level end sound plays (map completion)
    if (current.levelEndSoundPlayed != 0 && 
        old.levelEndSoundPlayed == 0)
    {
        print("[SOUND] Level end sound detected - raw mapName: '" + current.mapName + "'");
        string completedMap = current.mapName.ToLower().Trim();
        print("[MAP] Processed map: '" + completedMap + "'");
        
        // Check if it's a standalone map
        if (vars.standaloneMaps.Contains(completedMap) && 
            !vars.completedStandalone.Contains(completedMap))
        {
            print("[STANDALONE] Found in standalone list");
            // Prevent duplicate splits for same map
            if (completedMap == vars.lastCompletedMap)
            {
                print("[DUPLICATE] Blocked duplicate split for standalone: " + completedMap);
                return false;
            }
            
            vars.lastCompletedMap = completedMap;
            vars.completedStandalone.Add(completedMap);
            print("Completed standalone: " + completedMap);
            return true;
        }
        else if (vars.standaloneMaps.Contains(completedMap))
        {
            print("[STANDALONE] Already completed: " + completedMap);
        }
        
        // Check if it's part of a group
        print("[GROUP] Checking groups for: " + completedMap);
        foreach (var group in vars.mapGroups)
        {
            string groupName = group.Key;
            List<string> mapsInGroup = group.Value;
            
            // Skip if group already complete
            if (vars.completedGroups.Contains(groupName))
            {
                print("[GROUP] Skipping completed group: " + groupName);
                continue;
            }
            
            int currentProgress = vars.groupProgress[groupName];
            
            // Check if this is the NEXT map in the sequence
            if (currentProgress < mapsInGroup.Count && 
                completedMap == mapsInGroup[currentProgress])
            {
                print("[GROUP] Map matches next in sequence for " + groupName);
                // Prevent duplicate splits for same map
                if (completedMap == vars.lastCompletedMap)
                {
                    print("[DUPLICATE] Blocked duplicate split for group map: " + completedMap);
                    return false;
                }
                
                vars.lastCompletedMap = completedMap;
                vars.groupProgress[groupName]++;
                print("Completed " + groupName + ": " + completedMap + 
                      " (" + vars.groupProgress[groupName] + "/" + mapsInGroup.Count + ")");
                
                // Check if group is now complete
                if (vars.groupProgress[groupName] >= mapsInGroup.Count)
                {
                    vars.completedGroups.Add(groupName);
                    print(groupName + " group complete!");
                }
                
                return true;
            }
            else if (mapsInGroup.Contains(completedMap))
            {
                // Map is in this group but out of order - ignore it
                print("Ignored out-of-order " + groupName + " map: " + completedMap);
                return false;
            }
        }
        
        print("[MAP] Not found in any standalone or group");
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
