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
    // All 13 maps required for full-game run (any order allowed)
    vars.requiredMaps = new HashSet<string>
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
    
    // Track which maps have been completed
    vars.completedMaps = new HashSet<string>();
}

start
{
    // Start on first map completion
    if (current.gameState == 3 && old.gameState != 3)
    {
        vars.completedMaps.Clear();
        return true;
    }
}

split
{
    // Split when completing a map that hasn't been done yet
    if (current.gameState == 2 && old.gameState != 2)
    {
        string completedMap = old.currentMap;
        
        // Only split if this map is required AND hasn't been completed yet
        if (vars.requiredMaps.Contains(completedMap) && 
            !vars.completedMaps.Contains(completedMap))
        {
            vars.completedMaps.Add(completedMap);
            print("Completed: " + completedMap + " (" + vars.completedMaps.Count + "/13)");
            return true;
        }
    }
}

reset
{
    // Reset if returning to menu
    if (current.gameState == 0 || current.gameState == 1)
    {
        vars.completedMaps.Clear();
        return true;
    }
}

update
{
    // Display current progress and map info
    if (current.currentMap != old.currentMap)
    {
        print("Map changed to: " + current.currentMap);
    }
}