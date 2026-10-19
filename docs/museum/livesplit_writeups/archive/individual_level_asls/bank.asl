/*
 * ==============================================================================
 * FDNY FIREFIGHTER - AUTO SPLITTER TEMPLATE
 * ==============================================================================
 * 
 * SETUP INSTRUCTIONS:
 * 1. Replace bank with your target map name (e.g., "training")
 * 2. Load this script in LiveSplit via Edit Splits → Settings → Browse
 * 3. Monitor debug output in DebugView++ (https://github.com/CobaltFusion/DebugViewPP)
 * 
 * LOGIC:
 * - START: gameState=1, levelEndSoundPlayed=0, mapName contains placeholder
 * - SPLIT: levelEndSoundPlayed 0→non-zero, gameState=1, correct map
 * - RESET: gameState 0→1, levelEndSoundPlayed non-zero→0, correct map
 * 
 * ==============================================================================
 */

state("FDNYFirefighter")
{
    int gameState : 0x00102AAC, 0x6F0;
    string10 mapName : 0x00102AAC, 0x688, 0x0, 0xC;
    int totalVictims : 0x00103A78, 0x30, 0x3528;
    int rescuedVictims : 0x00103A78, 0x30, 0x352C;
    int levelEndSoundPlayed : 0x00103A78, 0x8, 0x0, 0x104, 0x0;
}

startup
{
    print("[FDNY] Script loaded - Target map: bank");
    vars.frameCount = 0;
    vars.hasSplit = false;
}

init
{
    print("[FDNY] Game process found, initializing");
    vars.frameCount = 0;
    vars.hasSplit = false;
}

update
{
    vars.frameCount++;
    
    // Heartbeat every 20 frames
    if (vars.frameCount % 20 == 0)
    {
        print(String.Format("[FDNY HEARTBEAT] Frame:{0} | gameState:{1} | map:'{2}' | victims:{3}/{4} | endSound:{5} | split:{6}",
            vars.frameCount,
            current.gameState,
            current.mapName,
            current.rescuedVictims,
            current.totalVictims,
            current.levelEndSoundPlayed,
            vars.hasSplit));
    }
    
    // Reset split flag when exiting to menu
    if (old.gameState == 1 && current.gameState == 0)
    {
        print("[FDNY] Exited to menu - reset split flag");
        vars.hasSplit = false;
    }
}

start
{
    // Only process when gameState is valid
    if (current.gameState != 1)
        return false;
    
    bool stateCheck = current.gameState == 1;
    bool soundCheck = current.levelEndSoundPlayed == 0;
    bool mapCheck = current.mapName.ToLower().Trim().Contains("bank");
    
    print(String.Format("[FDNY START] Checks - state:1={0} | sound:0={1} | map:match={2}",
        stateCheck, soundCheck, mapCheck));
    
    if (stateCheck && soundCheck && mapCheck)
    {
        print("[FDNY START] ✓✓✓ TIMER STARTED");
        vars.hasSplit = false;
        return true;
    }
    
    return false;
}

split
{
    // Only process when gameState is valid
    if (current.gameState != 1)
        return false;
    
    bool stateCheck = current.gameState == 1;
    bool soundTransition = old.levelEndSoundPlayed == 0 && current.levelEndSoundPlayed != 0;
    bool mapCheck = current.mapName.ToLower().Trim().Contains("bank");
    bool notSplit = !vars.hasSplit;
    
    print(String.Format("[FDNY SPLIT] Checks - state:1={0} | sound:0→1={1} | map:match={2} | notSplit={3}",
        stateCheck, soundTransition, mapCheck, notSplit));
    
    if (stateCheck && soundTransition && mapCheck && notSplit)
    {
        print("[FDNY SPLIT] ✓✓✓ SPLIT TRIGGERED");
        vars.hasSplit = true;
        return true;
    }
    
    return false;
}

reset
{
    if (current.gameState == 0)
    {
        return true;
    }
    
    return false;
}