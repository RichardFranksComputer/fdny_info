// FDNY Firefighter - Training Level Auto-Splitter
// Fixed: Proper pause handling + subsplits for each victim rescue + timer pause
state("FDNYFirefighter")
{
}

startup
{
    vars.mapName = "";
    vars.totalVictims = 0;
    vars.rescuedVictims = 0;
    vars.isRunActive = false;
    vars.isCompleted = false;
    vars.isPaused = 0;
    vars.gameState = 0;
    vars.lastRescuedCount = 0;
    
    settings.Add("debug", false, "Show debug output");
    settings.Add("subsplits", true, "Split on each victim rescue");
}

init
{
    vars.mapName = "";
    vars.totalVictims = 0;
    vars.rescuedVictims = 0;
    vars.isRunActive = false;
    vars.isCompleted = false;
    vars.isPaused = 0;
    vars.gameState = 0;
    vars.lastRescuedCount = 0;
}

update
{
    // Store old gameState before updating
    vars.oldGameState = vars.gameState;
    
    // Read game state through pointer
    try {
        IntPtr gmPtr = game.ReadPointer((IntPtr)0x00502aac);
        if (gmPtr != IntPtr.Zero) {
            vars.gameState = game.ReadValue<int>(gmPtr + 0x6f0);
        }
    } catch {
        vars.gameState = 0;
    }
    
    // Read pause flag - using masking
    try {
        int rawValue = game.ReadValue<int>((IntPtr)0x00502ad4);
        vars.isPaused = rawValue & 0xFF;  // Get only the lowest byte
    } catch {
        vars.isPaused = 0;
    }
    
    // Safely read map name (with NULL protection)
    try {
        IntPtr gmPtr = game.ReadPointer((IntPtr)0x00502aac);
        if (gmPtr != IntPtr.Zero) {
            IntPtr levelInfo = game.ReadPointer(gmPtr + 0x688);
            if (levelInfo != IntPtr.Zero) {
                IntPtr mapPtr = game.ReadPointer(levelInfo + 0x0);
                if (mapPtr != IntPtr.Zero) {
                    vars.mapName = game.ReadString(mapPtr + 0xC, 50);
                }
            }
        }
    } catch {
        vars.mapName = "";
    }
    
    // Safely read victim counts (with NULL protection)
    try {
        IntPtr victimBase = game.ReadPointer((IntPtr)0x00503a78);
        if (victimBase != IntPtr.Zero) {
            IntPtr victimTracker = game.ReadPointer(victimBase + 0x30);
            if (victimTracker != IntPtr.Zero) {
                vars.totalVictims = game.ReadValue<int>(victimTracker + 0x3528);
                vars.rescuedVictims = game.ReadValue<int>(victimTracker + 0x3530);
            }
        }
    } catch {
        vars.totalVictims = 0;
        vars.rescuedVictims = 0;
    }
    
    // Debug output
    if (settings["debug"]) {
        print("State: " + vars.gameState + 
              " | Map: " + vars.mapName + 
              " | Paused: " + vars.isPaused + 
              " | Victims: " + vars.rescuedVictims + "/" + vars.totalVictims);
    }
}

start
{
    // Start when training level loads and gameplay begins
    if (vars.mapName == "training" && 
        vars.gameState == 1 && 
        vars.oldGameState != 1)
    {
        vars.isRunActive = true;
        vars.isCompleted = false;
        vars.lastRescuedCount = 0;  // Reset rescue counter
        
        if (settings["debug"])
            print("Timer started - Training level active");
        
        return true;
    }
}

split
{
    // Subsplit on each victim rescue (if enabled)
    if (settings["subsplits"] && 
        vars.isRunActive && 
        !vars.isCompleted &&
        vars.rescuedVictims > vars.lastRescuedCount &&
        vars.rescuedVictims < vars.totalVictims)  // Don't split on last victim (save for final split)
    {
        vars.lastRescuedCount = vars.rescuedVictims;
        
        if (settings["debug"])
            print("Subsplit - Victim " + vars.rescuedVictims + "/" + vars.totalVictims + " rescued");
        
        return true;
    }
    
    // Final split when all victims rescued and level completes
    if (vars.isRunActive && 
        !vars.isCompleted &&
        vars.rescuedVictims == vars.totalVictims && 
        vars.totalVictims > 0 &&
        vars.gameState == 2 && 
        vars.oldGameState == 1)
    {
        vars.isCompleted = true;
        vars.isRunActive = false;
        
        if (settings["debug"])
            print("Final split - Level complete");
        
        return true;
    }
}

reset
{
    // Auto-reset if returning to menu before completion
    // BUT don't reset if game is just paused (pause flag = 1)
    if (vars.isRunActive && 
        !vars.isCompleted && 
        vars.gameState == 0 &&
        vars.isPaused == 0)  // Only reset if NOT paused
    {
        vars.isRunActive = false;
        vars.lastRescuedCount = 0;  // Reset rescue counter
        
        if (settings["debug"])
            print("Timer reset - Returned to menu");
        
        return true;
    }
    
    // Reset after completion when training loads again
    if (vars.isCompleted && 
        vars.mapName == "training" && 
        vars.gameState == 1)
    {
        vars.isCompleted = false;
        vars.lastRescuedCount = 0;  // Reset rescue counter
        
        if (settings["debug"])
            print("Ready for new run");
    }
}

isLoading
{
    // Always pause timer during loading states
    if (vars.gameState == 2) {
        return true;
    }
    
    // Pause timer when game is paused (only during active run)
    if (vars.isRunActive && !vars.isCompleted && vars.isPaused == 1)
    {
        return true;
    }
    
    return false;
}