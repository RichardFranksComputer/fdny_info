/*
 * ==============================================================================
 * FDNY FIREFIGHTER - AUTO SPLITTER (ALL MAPS)
 * ==============================================================================
 * 
 * SETUP INSTRUCTIONS:
 * 1. Load this script in LiveSplit via Edit Splits → Settings → Browse
 * 2. Set your layout to display "Game Time" (not Real Time)
 * 3. Monitor debug output in DebugView++ (https://github.com/CobaltFusion/DebugViewPP)
 * 
 * Resets any time gameState is 0 (game in menu)
 * INTENDED FOR IL RUNS ONLY
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
    
    string currentMapLower = current.mapName.ToLower().Trim();
    
    // Heartbeat every 60 frames (~1 second)
    if (vars.frameCount % 60 == 0)
    {
        print(String.Format("[FDNY] Frame:{0} | State:{1} | Map:'{2}' | Split:{3} | LastMap:'{4}'",
            vars.frameCount,
            current.gameState,
            currentMapLower,
            vars.hasSplit,
            vars.lastMap));
    }
    
    // Reset split flag when entering gameplay from menu (0→1)
    if (old.gameState == 0 && current.gameState == 1)
    {
        print(String.Format("[FDNY] Menu→Gameplay | Map:'{0}' | RESET split flag", currentMapLower));
        vars.hasSplit = false;
        vars.lastMap = currentMapLower;
    }
    
    // Reset split flag when map changes DURING gameplay (multi-stage direct transitions)
    // This happens AFTER the split has been processed
    if (current.gameState == 1 && vars.hasSplit && vars.lastMap != "" && vars.lastMap != currentMapLower)
    {
        print(String.Format("[FDNY] Map transition completed '{0}'→'{1}' | RESET split flag, RESUME timer", 
            vars.lastMap, currentMapLower));
        vars.hasSplit = false;
        vars.lastMap = currentMapLower;
    }
}

start
{
    // Start when in gameplay state
    if (current.gameState == 1)
    {
        string currentMap = current.mapName.ToLower().Trim();
        print(String.Format("[FDNY START] ✓✓✓ TIMER STARTED ✓✓✓ | Map:'{0}'", currentMap));
        
        vars.hasSplit = false;
        vars.lastMap = currentMap;
        vars.frameCount = 0;
        
        return true;
    }
    
    return false;
}

split
{
    // Guard: Only split during gameplay and if we haven't already split
    if (current.gameState != 1 || vars.hasSplit)
        return false;
    
    string currentMap = current.mapName.ToLower().Trim();
    
    // Initialize lastMap if empty (shouldn't happen, but safety check)
    if (vars.lastMap == "")
    {
        vars.lastMap = currentMap;
        return false;
    }
    
    // ============================================================================
    // MAP TRANSITION SPLITS (Multi-stage levels)
    // Check FIRST - these happen before sound triggers
    // Note: lastMap is NOT updated here - update block handles it after transition
    // ============================================================================
    
    // BOAT: A→B
    if (vars.lastMap.Contains("boat_a") && currentMap.Contains("boat_b"))
    {
        print(String.Format("[FDNY SPLIT] ✓✓✓ Boat A→B | '{0}'→'{1}'", vars.lastMap, currentMap));
        vars.hasSplit = true;
        // Don't update lastMap - let update block handle it when map stabilizes
        return true;
    }
    
    // SUBWAY: A→B
    if (vars.lastMap.Contains("subway_a") && currentMap.Contains("subway_b"))
    {
        print(String.Format("[FDNY SPLIT] ✓✓✓ Subway A→B | '{0}'→'{1}'", vars.lastMap, currentMap));
        vars.hasSplit = true;
        return true;
    }
    
    // OIL RIG: A→B
    if (vars.lastMap.Contains("oil_rig_a") && currentMap.Contains("oil_rig_b"))
    {
        print(String.Format("[FDNY SPLIT] ✓✓✓ Oil Rig A→B | '{0}'→'{1}'", vars.lastMap, currentMap));
        vars.hasSplit = true;
        return true;
    }
    
    // OIL RIG: B→C
    if (vars.lastMap.Contains("oil_rig_b") && currentMap.Contains("oil_rig_c"))
    {
        print(String.Format("[FDNY SPLIT] ✓✓✓ Oil Rig B→C | '{0}'→'{1}'", vars.lastMap, currentMap));
        vars.hasSplit = true;
        return true;
    }
    
    // OIL RIG: C→D
    if (vars.lastMap.Contains("oil_rig_c") && currentMap.Contains("oil_rig_d"))
    {
        print(String.Format("[FDNY SPLIT] ✓✓✓ Oil Rig C→D | '{0}'→'{1}'", vars.lastMap, currentMap));
        vars.hasSplit = true;
        return true;
    }
    
    // ============================================================================
    // SINGLE-STAGE MAPS - Sound triggers
    // ============================================================================
    
    // Training
    if (currentMap.Contains("training") && 
        old.trainingLevelEndSoundPlayed == 0 && current.trainingLevelEndSoundPlayed != 0)
    {
        print("[FDNY SPLIT] ✓✓✓ Training completed");
        vars.hasSplit = true;
        return true;
    }
    
    // Bank
    if (currentMap.Contains("bank") && 
        old.bankLevelEndSoundPlayed == 0 && current.bankLevelEndSoundPlayed != 0)
    {
        print("[FDNY SPLIT] ✓✓✓ Bank completed");
        vars.hasSplit = true;
        return true;
    }
    
    // Bar
    if (currentMap.Contains("bar_r") && 
        old.barLevelEndSoundPlayed == 0 && current.barLevelEndSoundPlayed != 0)
    {
        print("[FDNY SPLIT] ✓✓✓ Bar completed");
        vars.hasSplit = true;
        return true;
    }
    
    // Gas Station
    if (currentMap.Contains("gas_r") && 
        old.gasStationLevelEndSoundPlayed == 0 && current.gasStationLevelEndSoundPlayed != 0)
    {
        print("[FDNY SPLIT] ✓✓✓ Gas Station completed");
        vars.hasSplit = true;
        return true;
    }
    
    // Military Base
    if (currentMap.Contains("mbase") && 
        old.militaryBaseLevelEndSoundPlayed == 0 && current.militaryBaseLevelEndSoundPlayed != 0)
    {
        print("[FDNY SPLIT] ✓✓✓ Military Base completed");
        vars.hasSplit = true;
        return true;
    }
    
    // ============================================================================
    // MULTI-STAGE FINAL COMPLETIONS - Sound triggers
    // ============================================================================
    
    // Boat B (final)
    if (currentMap.Contains("boat_b") && 
        old.boatLevelEndSoundPlayed == 0 && current.boatLevelEndSoundPlayed != 0)
    {
        print("[FDNY SPLIT] ✓✓✓ Boat B completed");
        vars.hasSplit = true;
        return true;
    }
    
    // Subway B (final)
    if (currentMap.Contains("subway_b") && 
        old.subwayLevelEndSoundPlayed == 0 && current.subwayLevelEndSoundPlayed != 0)
    {
        print("[FDNY SPLIT] ✓✓✓ Subway B completed");
        vars.hasSplit = true;
        return true;
    }
    
    // Oil Rig D (final)
    if (currentMap.Contains("oil_rig_d") && 
        old.oilRigDLevelEndSoundPlayed == 0 && current.oilRigDLevelEndSoundPlayed != 0)
    {
        print("[FDNY SPLIT] ✓✓✓ Oil Rig D completed");
        vars.hasSplit = true;
        return true;
    }
    
    return false;
}

isLoading
{
    // Pause Game Time when:
    // 1. We've split (excludes menu/loading time between levels)
    // 2. gameState is 2 (loading) or 3 (win screen)
    // Timer resumes when:
    // - Entering next level from menu (update: gameState 0→1)
    // - Map transition completes during gameplay (update: map change while hasSplit=true)
    return vars.hasSplit || current.gameState == 2 || current.gameState == 3;
}

reset
{
    if (current.gameState == 0)
    {
        print("[FDNY RESET] ✓ Returned to menu");
        return true;
    }
    
    return false;
}