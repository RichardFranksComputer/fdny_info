state("game_executable_name")  // Replace with actual .exe name
{
    // Game state for start/split detection
    int gameState : 0x00502ab8, 0xc, 0x6f0;
    
    // Map name - C++ string pointer
    // Read: GameManager pointer → +0x660 → string data at +0xC
    string255 currentMap : 0x00502aac, 0x660, 0xC;
}

startup
{
    // Your curated speedrun map list (adjust these to actual map names)
    vars.mapRoute = new List<string> 
    {
        "tutorial",
        "warehouse", 
        "facility",
        "downtown",
        "finale"
        // Add your actual map names here
    };
    
    vars.currentSplitIndex = 0;
}

start
{
    // Start timer when entering the first map of the route
    if (current.gameState == 3 && old.gameState != 3)
    {
        if (current.currentMap == vars.mapRoute[0])
        {
            vars.currentSplitIndex = 0;
            return true;
        }
    }
}

split
{
    // Split when completing a map that's in the speedrun route
    if (current.gameState == 2 && old.gameState != 2)
    {
        // Check if the completed map is in our route
        if (vars.mapRoute.Contains(old.currentMap))
        {
            vars.currentSplitIndex++;
            return true;
        }
    }
}

reset
{
    // Reset if returning to menu
    if (current.gameState == 0 || current.gameState == 1)
    {
        vars.currentSplitIndex = 0;
        return true;
    }
}

update
{
    // Optional: Display current map in LiveSplit (for debugging)
    if (current.currentMap != old.currentMap)
    {
        print("Map changed to: " + current.currentMap);
    }
}