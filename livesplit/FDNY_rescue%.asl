/*
 * ==============================================================================
 * FDNY FIREFIGHTER - RESCUE% AUTO SPLITTER (ALL RESCUE MAPS)
 * ==============================================================================
 * Manual resets required
 * No automatic resetting logic
 * ==============================================================================
 */

state("FDNYFirefighter")
{
    int gameState : 0x00102AAC, 0x6F0;
    string10 mapName : 0x00102AAC, 0x688, 0x0, 0xC;
    int totalVictims : 0x00103A78, 0x30, 0x3528;
    int rescuedVictims : 0x00103A78, 0x30, 0x352C;
    
    // Single-stage map completion sounds
    int bankLevelEndSoundPlayed : 0x00103A78, 0x8, 0x0, 0x158, 0x0;
    int barLevelEndSoundPlayed : 0x00103A78, 0x8, 0x0, 0xFC, 0x0;
    int gasStationLevelEndSoundPlayed : 0x00103A78, 0x8, 0x0, 0xF0, 0x0;
    int militaryBaseLevelEndSoundPlayed : 0x00103A78, 0x8, 0x0, 0xC8, 0x0;
    int trainingLevelEndSoundPlayed : 0x00103A78, 0x8, 0x0, 0x104, 0x0;
    
    // Multi-stage final completion sounds
    int boatLevelEndSoundPlayed : 0x00103A78, 0x8, 0x0, 0xBC, 0x0;
    int oilRigDLevelEndSoundPlayed : 0x00103A78, 0x8, 0x0, 0xC4, 0x0;
    int subwayLevelEndSoundPlayed : 0x00103A78, 0x8, 0x0, 0x144, 0x0;
}

startup
{
    print("[FDNY] ========================================");
    print("[FDNY] Auto-splitter script loaded");
    print("[FDNY] ========================================");
    
    vars.frameCount = 0;
    vars.hasSplit = false;
    vars.lastMap = "";
}

init
{
    print("[FDNY] Game process attached, initializing");
    
    vars.frameCount = 0;
    vars.hasSplit = false;
    vars.lastMap = "";
}

update
{
    vars.frameCount++;
    
    vars.currentMap = current.mapName.ToLower().Trim();

    // Heartbeat every 300 frames (~5 seconds)
    if (vars.frameCount % 300 == 0)
    {
        print(String.Format("[FDNY] Frame:{0} | State:{1} | Map:'{2}' | Split:{3} | LastMap:'{4}'",
            vars.frameCount,
            current.gameState,
            vars.currentMap,
            vars.hasSplit,
            vars.lastMap));
    }
    
    // Reset split flag when entering gameplay from menu (0→1)
    if (old.gameState == 0 && current.gameState == 1)
    {
        print(String.Format("[FDNY] Menu→Gameplay | Map:'{0}' | RESET split flag", vars.currentMap));
        vars.hasSplit = false;
        vars.lastMap = vars.currentMap;
    }
    
    // Reset split flag when map changes DURING gameplay (multi-stage direct transitions)
    // This happens AFTER the split has been processed
    if (current.gameState == 1 && vars.hasSplit && vars.lastMap != "" && vars.lastMap != vars.currentMap)
    {
        print(String.Format("[FDNY] Map transition completed '{0}'→'{1}' | RESET split flag, RESUME timer", 
            vars.lastMap, vars.currentMap));
        vars.hasSplit = false;
        vars.lastMap = vars.currentMap;
    }
}

start
{
    // Start when in gameplay state
    if (current.gameState == 1)
    {
        print(String.Format("[FDNY START] TIMER STARTED | Map:'{0}'", vars.currentMap));
        
        vars.hasSplit = false;
        vars.lastMap = vars.currentMap;
        vars.frameCount = 0;
        
        return true;
    }
    
    return false;
}

split
{
    // Only split during gameplay and if we haven't already split
    if (current.gameState != 1 || vars.hasSplit)
        return false;
    
    // ============================================================================
    // MAP TRANSITION SPLITS (Multi-stage levels)
    // Check FIRST - these happen before sound triggers
    // Note: lastMap is NOT updated here - update block handles it after transition
    // ============================================================================
    
    if (vars.lastMap.Contains("boat_a") && vars.currentMap.Contains("boat_b"))
    {
        print(String.Format("[FDNY SPLIT] Boat A→B | '{0}'→'{1}'", vars.lastMap, vars.currentMap));
        vars.hasSplit = true;
        return true;
    }
    
    if (vars.lastMap.Contains("subway_a") && vars.currentMap.Contains("subway_b"))
    {
        print(String.Format("[FDNY SPLIT] Subway A→B | '{0}'→'{1}'", vars.lastMap, vars.currentMap));
        vars.hasSplit = true;
        return true;
    }
    
    if (vars.lastMap.Contains("oil_rig_a") && vars.currentMap.Contains("oil_rig_b"))
    {
        print(String.Format("[FDNY SPLIT] Oil Rig A→B | '{0}'→'{1}'", vars.lastMap, vars.currentMap));
        vars.hasSplit = true;
        return true;
    }
    
    if (vars.lastMap.Contains("oil_rig_b") && vars.currentMap.Contains("oil_rig_c"))
    {
        print(String.Format("[FDNY SPLIT] Oil Rig B→C | '{0}'→'{1}'", vars.lastMap, vars.currentMap));
        vars.hasSplit = true;
        return true;
    }
    
    if (vars.lastMap.Contains("oil_rig_c") && vars.currentMap.Contains("oil_rig_d"))
    {
        print(String.Format("[FDNY SPLIT] Oil Rig C→D | '{0}'→'{1}'", vars.lastMap, vars.currentMap));
        vars.hasSplit = true;
        return true;
    }
    
    // ============================================================================
    // SINGLE-STAGE MAPS - Sound triggers
    // Each map has a corresponding memory address to monitor for EndSoundPlayed condition
    // ============================================================================
    
    if (vars.currentMap.Contains("training") && 
        old.trainingLevelEndSoundPlayed == 0 && current.trainingLevelEndSoundPlayed != 0)
    {
        print("[FDNY SPLIT] Training completed");
        vars.hasSplit = true;
        return true;
    }
    
    if (vars.currentMap.Contains("bank") && 
        old.bankLevelEndSoundPlayed == 0 && current.bankLevelEndSoundPlayed != 0)
    {
        print("[FDNY SPLIT] Bank completed");
        vars.hasSplit = true;
        return true;
    }
    
    if (vars.currentMap.Contains("bar_r") && 
        old.barLevelEndSoundPlayed == 0 && current.barLevelEndSoundPlayed != 0)
    {
        print("[FDNY SPLIT] Bar completed");
        vars.hasSplit = true;
        return true;
    }
    
    if (vars.currentMap.Contains("gas_r") && 
        old.gasStationLevelEndSoundPlayed == 0 && current.gasStationLevelEndSoundPlayed != 0)
    {
        print("[FDNY SPLIT] Gas Station completed");
        vars.hasSplit = true;
        return true;
    }
    
    if (vars.currentMap.Contains("mbase") && 
        old.militaryBaseLevelEndSoundPlayed == 0 && current.militaryBaseLevelEndSoundPlayed != 0)
    {
        print("[FDNY SPLIT] Military Base completed");
        vars.hasSplit = true;
        return true;
    }
    
    // ============================================================================
    // MULTI-STAGE FINAL COMPLETIONS - Sound triggers
    // Final stages of multi-stage levels will are split when their end sound plays
    // ============================================================================
    
    if (vars.currentMap.Contains("boat_b") && 
        old.boatLevelEndSoundPlayed == 0 && current.boatLevelEndSoundPlayed != 0)
    {
        print("[FDNY SPLIT] Boat B completed");
        vars.hasSplit = true;
        return true;
    }
    
    if (vars.currentMap.Contains("subway_b") && 
        old.subwayLevelEndSoundPlayed == 0 && current.subwayLevelEndSoundPlayed != 0)
    {
        print("[FDNY SPLIT] Subway B completed");
        vars.hasSplit = true;
        return true;
    }
    
    if (vars.currentMap.Contains("oil_rig_d") && 
        old.oilRigDLevelEndSoundPlayed == 0 && current.oilRigDLevelEndSoundPlayed != 0)
    {
        print("[FDNY SPLIT] Oil Rig D completed");
        vars.hasSplit = true;
        return true;
    }
    
    return false;
}

isLoading
{
    // hasSplit = true occurs after levelEndSoundPlayed (single stage levels)
    // current.gamestate 2 occurs during loading (intermediary stages of multistage maps)
    // current.gamestate 3 during victory 
    return vars.hasSplit || current.gameState == 2 || current.gameState == 3;
}

reset
{
    return false;
}