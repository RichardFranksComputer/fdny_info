state("FDNYFirefighter", "1.0")
{
    // Game state (0 = menu, 1 = in-game, etc.)
    int gameState : 0x00502AAC, 0x6F0;
    
    // Map name (string)
    string10 mapName : 0x00502AAC, 0x688, 0x0, 0xC;
    
    // Victim tracking
    int totalVictims : 0x00503A78, 0x30, 0x3528;
    int currentVictim : 0x00503A78, 0x30, 0x3530;
    int rescuedVictims : 0x00503A78, 0x30, 0x352C;
    
    // Sound trigger (level end sound)
    int levelEndSound : 0x00503A78, 0x8, 0x0, 0x104, 0x0;
}

startup
{
    settings.Add("autostart", true, "Auto-start timer on training level");
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
    // Start when: game state becomes 1 AND map is "training"
    if (settings["autostart"] && 
        current.gameState == 1 && 
        old.gameState != 1 && 
        current.mapName.ToLower().Contains("training") &&
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
        current.levelEndSound != 0x00000000 &&  // Explicit hex zero
        old.levelEndSound == 0x00000000 &&
        !vars.hasSplit)
    {
        vars.hasSplit = true;
        return true;
    }
}

reset
{
    // Reset when returning to menu
    if (current.gameState == 0 && old.gameState != 0)
    {
        vars.hasStarted = false;
        vars.hasSplit = false;
        return true;
    }
}

isLoading
{
    // Optional: Pause timer during loading screens if you can detect them
    // For now, we're not using this
    return false;
}