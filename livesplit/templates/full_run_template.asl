state("FDNYFirefighter", "1.0")
{  
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
        { "{{GROUP_NAME_PLACEHOLDER}}", new List<string> { "{{MAP_NAME_PLACEHOLDER}}" } }
    };
    
    // Standalone maps (any order)
    vars.standaloneMaps = new HashSet<string>
    {
        "{{MAP_NAME_PLACEHOLDER}}"
    };
    
    // Track completed standalone maps
    vars.completedStandalone = new HashSet<string>();
    
    // Track progress within each group
    vars.groupProgress = new Dictionary<string, int>
    {
        { "{{GROUP_NAME_PLACEHOLDER}}", 0 }
    };
    
    // Track which groups are complete
    vars.completedGroups = new HashSet<string>();
    
    // Prevent double-triggers
    vars.hasStarted = false;
    vars.lastCompletedMap = "";
}

init
{
    // Reset flags when game loads
    vars.hasStarted = false;
    vars.completedStandalone.Clear();
    vars.completedGroups.Clear();
    vars.groupProgress["{{GROUP_NAME_PLACEHOLDER}}"] = 0;
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
            else if (mapsInGroup.Contains(completedMap))
            {
                // Map is in this group but out of order - ignore it
                print("Ignored out-of-order " + groupName + " map: " + completedMap);
                return false;
            }
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
