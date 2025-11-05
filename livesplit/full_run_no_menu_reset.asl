/*
 * ==============================================================================
 * FDNY FIREFIGHTER - AUTO SPLITTER (ALL MAPS)
 * ==============================================================================
 * 
 * SETUP INSTRUCTIONS:
 * 1. Load this script in LiveSplit via Edit Splits → Settings → Browse
 * 2. Monitor debug output in DebugView++ (https://github.com/CobaltFusion/DebugViewPP)
 * 
 * LOGIC:
 * - START: gameState=1, trainingLevelEndSoundPlayed=0, mapName contains "training"
 * - SPLIT (Single-stage maps): mapName matches AND sound 0→non-zero
 * - SPLIT (Multi-stage intermediate): mapName transitions to next stage
 * - SPLIT (Multi-stage final): mapName matches final stage AND sound 0→non-zero
 * - RESET: gameState becomes 0 (return to menu)
 * 
 * ==============================================================================
 */

state("FDNYFirefighter")
{
    int gameState : 0x00102AAC, 0x6F0;
    string10 mapName : 0x00102AAC, 0x688, 0x0, 0xC;
    int totalVictims : 0x00103A78, 0x30, 0x3528;
    int rescuedVictims : 0x00103A78, 0x30, 0x352C;
    
    // Single-stage maps
    int bankLevelEndSoundPlayed : 0x00103A78, 0x8, 0x0, 0x158, 0x0;
    int barLevelEndSoundPlayed : 0x00103A78, 0x8, 0x0, 0xFC, 0x0;
    int gasStationLevelEndSoundPlayed : 0x00103A78, 0x8, 0x0, 0xF0, 0x0;
    int militaryBaseLevelEndSoundPlayed : 0x00103A78, 0x8, 0x0, 0xC8, 0x0;
    int trainingLevelEndSoundPlayed : 0x00103A78, 0x8, 0x0, 0x104, 0x0;
    
    // Multi-stage final maps only
    int boatLevelEndSoundPlayed : 0x00103A78, 0x8, 0x0, 0xBC, 0x0;
    int oilRigDLevelEndSoundPlayed : 0x00103A78, 0x8, 0x0, 0xC4, 0x0;
    int subwayLevelEndSoundPlayed : 0x00103A78, 0x8, 0x0, 0x144, 0x0;
}

startup
{
    print("[FDNY] Script loaded - All maps configured");
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
    
    // Heartbeat every 60 frames
    if (vars.frameCount % 60 == 0)
    {
        print(String.Format("[FDNY HEARTBEAT] Frame:{0} | gameState:{1} | map:'{2}' | victims:{3}/{4}",
            vars.frameCount,
            current.gameState,
            current.mapName,
            current.rescuedVictims,
            current.totalVictims));
    }
    
    // Reset split flag when map changes or returning to menu
    if (old.mapName != current.mapName || (old.gameState == 1 && current.gameState == 0))
    {
        print(String.Format("[FDNY] Map changed '{0}'→'{1}' or menu transition - reset split flag", 
            old.mapName, current.mapName));
        vars.hasSplit = false;
    }
}

start
{
    if (current.gameState != 1)
        return false;
    
    bool stateCheck = current.gameState == 1;
    bool soundCheck = current.trainingLevelEndSoundPlayed == 0;
    bool mapCheck = current.mapName.ToLower().Trim().Contains("training");
    
    if (stateCheck && soundCheck && mapCheck)
    {
        print("[FDNY START] ✓✓✓ TIMER STARTED on training");
        vars.hasSplit = false;
        return true;
    }
    
    return false;
}

split
{
    if (current.gameState != 1 || vars.hasSplit)
        return false;
    
    string oldMap = old.mapName.ToLower().Trim();
    string currentMap = current.mapName.ToLower().Trim();
    
    // ============================================================================
    // SINGLE-STAGE MAPS: Split on sound 0→non-zero
    // ============================================================================
    
    // Bank
    if (currentMap.Contains("bank") && 
        old.bankLevelEndSoundPlayed == 0 && current.bankLevelEndSoundPlayed != 0)
    {
        print("[FDNY SPLIT] ✓ Bank completed (sound triggered)");
        vars.hasSplit = true;
        return true;
    }
    
    // Bar
    if (currentMap.Contains("bar_r") && 
        old.barLevelEndSoundPlayed == 0 && current.barLevelEndSoundPlayed != 0)
    {
        print("[FDNY SPLIT] ✓ Bar completed (sound triggered)");
        vars.hasSplit = true;
        return true;
    }
    
    // Gas Station
    if (currentMap.Contains("gas_r") && 
        old.gasStationLevelEndSoundPlayed == 0 && current.gasStationLevelEndSoundPlayed != 0)
    {
        print("[FDNY SPLIT] ✓ Gas Station completed (sound triggered)");
        vars.hasSplit = true;
        return true;
    }
    
    // Military Base
    if (currentMap.Contains("mbase") && 
        old.militaryBaseLevelEndSoundPlayed == 0 && current.militaryBaseLevelEndSoundPlayed != 0)
    {
        print("[FDNY SPLIT] ✓ Military Base completed (sound triggered)");
        vars.hasSplit = true;
        return true;
    }
    
    // Training
    if (currentMap.Contains("training") && 
        old.trainingLevelEndSoundPlayed == 0 && current.trainingLevelEndSoundPlayed != 0)
    {
        print("[FDNY SPLIT] ✓ Training completed (sound triggered)");
        vars.hasSplit = true;
        return true;
    }
    
    // ============================================================================
    // BOAT GROUP: Map transitions + final sound
    // ============================================================================
    
    // boat_a → boat_b
    if (oldMap.Contains("boat_a") && currentMap.Contains("boat_b"))
    {
        print("[FDNY SPLIT] ✓ Boat stage A→B (map transition)");
        vars.hasSplit = true;
        return true;
    }
    
    // boat_b completion (final stage)
    if (currentMap.Contains("boat_b") && 
        old.boatLevelEndSoundPlayed == 0 && current.boatLevelEndSoundPlayed != 0)
    {
        print("[FDNY SPLIT] ✓ Boat B completed (sound triggered)");
        vars.hasSplit = true;
        return true;
    }
    
    // ============================================================================
    // OIL RIG GROUP: Map transitions + final sound
    // ============================================================================
    
    // oil_rig_a → oil_rig_b
    if (oldMap.Contains("oil_rig_a") && currentMap.Contains("oil_rig_b"))
    {
        print("[FDNY SPLIT] ✓ Oil Rig stage A→B (map transition)");
        vars.hasSplit = true;
        return true;
    }
    
    // oil_rig_b → oil_rig_c
    if (oldMap.Contains("oil_rig_b") && currentMap.Contains("oil_rig_c"))
    {
        print("[FDNY SPLIT] ✓ Oil Rig stage B→C (map transition)");
        vars.hasSplit = true;
        return true;
    }
    
    // oil_rig_c → oil_rig_d
    if (oldMap.Contains("oil_rig_c") && currentMap.Contains("oil_rig_d"))
    {
        print("[FDNY SPLIT] ✓ Oil Rig stage C→D (map transition)");
        vars.hasSplit = true;
        return true;
    }
    
    // oil_rig_d completion (final stage)
    if (currentMap.Contains("oil_rig_d") && 
        old.oilRigDLevelEndSoundPlayed == 0 && current.oilRigDLevelEndSoundPlayed != 0)
    {
        print("[FDNY SPLIT] ✓ Oil Rig D completed (sound triggered)");
        vars.hasSplit = true;
        return true;
    }
    
    // ============================================================================
    // SUBWAY GROUP: Map transitions + final sound
    // ============================================================================
    
    // subway_a → subway_b
    if (oldMap.Contains("subway_a") && currentMap.Contains("subway_b"))
    {
        print("[FDNY SPLIT] ✓ Subway stage A→B (map transition)");
        vars.hasSplit = true;
        return true;
    }
    
    // subway_b completion (final stage)
    if (currentMap.Contains("subway_b") && 
        old.subwayLevelEndSoundPlayed == 0 && current.subwayLevelEndSoundPlayed != 0)
    {
        print("[FDNY SPLIT] ✓ Subway B completed (sound triggered)");
        vars.hasSplit = true;
        return true;
    }
    
    return false;
}

reset
{  
    return false;
}