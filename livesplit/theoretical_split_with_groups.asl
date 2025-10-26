state("FDNYFirefighter")
{
    // Game state for start/split detection
    int gameState : 0x00502ab8, 0xc, 0x6f0;
    
    // Map name - C++ string pointer
    // Read: GameManager pointer → +0x660 → string data at +0xC
    string255 currentMap : 0x00502aac, 0x660, 0xC;
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
}

start
{
    // Start on first map completion
    if (current.gameState == 3 && old.gameState != 3)
    {
        vars.completedStandalone.Clear();
        vars.completedGroups.Clear();
        vars.groupProgress["boat"] = 0;
        vars.groupProgress["oil_rig"] = 0;
        vars.groupProgress["subway"] = 0;
        return true;
    }
}

split
{
    // Split when completing a map
    if (current.gameState == 2 && old.gameState != 2)
    {
        string completedMap = old.currentMap;
        
        // Check if it's a standalone map
        if (vars.standaloneMaps.Contains(completedMap) && 
            !vars.completedStandalone.Contains(completedMap))
        {
            vars.completedStandalone.Add(completedMap);
            print("Completed standalone: " + completedMap);
            return true;
        }
        
        // Check if it's part of a group
        foreach (var group in vars.mapGroups)
        {
            string groupName = group.Key;
            List<string> mapsInGroup = group.Value;
            
            // Skip if group already complete
            if (vars.completedGroups.Contains(groupName))
                continue;
            
            int currentProgress = vars.groupProgress[groupName];
            
            // Check if this is the NEXT map in the sequence
            if (currentProgress < mapsInGroup.Count && 
                completedMap == mapsInGroup[currentProgress])
            {
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
        }
    }
}

reset
{
    // Reset if returning to menu
    if (current.gameState == 0 || current.gameState == 1)
    {
        vars.completedStandalone.Clear();
        vars.completedGroups.Clear();
        vars.groupProgress["boat"] = 0;
        vars.groupProgress["oil_rig"] = 0;
        vars.groupProgress["subway"] = 0;
        return true;
    }
}

update
{
    // Display current progress
    if (current.currentMap != old.currentMap)
    {
        print("Map changed to: " + current.currentMap);
    }
    
    // Calculate total progress
    int totalSplits = vars.completedStandalone.Count + 
                      vars.groupProgress["boat"] + 
                      vars.groupProgress["oil_rig"] + 
                      vars.groupProgress["subway"];
    print("Progress: " + totalSplits + "/13");
}