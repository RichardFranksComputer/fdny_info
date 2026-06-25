/*
 * ==============================================================================
 * FDNY FIREFIGHTER - RESCUE% AUTO SPLITTER (ALL RESCUE MAPS)
 * ==============================================================================
 * Manual resets required (no automatic reset logic)
 *
 * Survivor Subsplit Logic (single-stage rescue levels):
 *   - Military Base: 5 survivors  → split on rescues 1–4, final split on level end sound
 *   - Downtown Bar: 6 survivors   → split on rescues 1–5, final split on level end sound
 *   - Gas Station: 7 survivors    → split on rescues 1–6, final split on level end sound
 *   - Bank Robbery: 6 survivors   → split on rescues 1–5, final split on level end sound
 *
 * Rules:
 *   - Survivor subsplits controlled by vars.useSurvivorSplits.
 *   - Survivor subsplits trigger on rescuedVictims increments, but ONLY when
 *     rescuedVictims < totalVictims (never on the final rescue).
 *   - Final split ALWAYS comes from the level-end sound flag, never from the
 *     final survivor rescue.
 *   - Training and multistage levels do NOT use survivor subsplits.
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
    print("[FDNY] Mode: RESCUE% with survivor subsplits");
    print("[FDNY] ========================================");

    vars.frameCount = 0;
    vars.hasSplit = false;      // "stage/IL completed" flag, not used for survivor subsplits
    vars.lastMap = "";
    vars.currentMap = "";

    // Global toggle for survivor subsplits
    // Change this to false if you don’t want survivor subsplits.
    vars.useSurvivorSplits = true;
}

init
{
    print("[FDNY] Game process attached, initializing");
    
    vars.frameCount = 0;
    vars.hasSplit = false;

    if (current.mapName == null)
        vars.currentMap = "";
    else
        vars.currentMap = current.mapName.ToLower().Trim();

    vars.lastMap = vars.currentMap;

    // Ensure survivor subsplits toggle always exists with a sane default
    // (overwriting is safe; there is no user-facing setting here)
    vars.useSurvivorSplits = true;
}

update
{
    vars.frameCount++;
    
    if (current.mapName == null)
        vars.currentMap = "";
    else
        vars.currentMap = current.mapName.ToLower().Trim();

    // Heartbeat every 300 frames (~5 seconds)
    if (vars.frameCount % 300 == 0)
    {
        print(String.Format("[FDNY] Frame:{0} | State:{1} | Map:'{2}' | Split:{3} | LastMap:'{4}' | Rescued:{5}/{6}",
            vars.frameCount,
            current.gameState,
            vars.currentMap,
            vars.hasSplit,
            vars.lastMap,
            current.rescuedVictims,
            current.totalVictims));
    }
    
    // Reset stage-completion split flag when entering gameplay from menu (0→1)
    if (old.gameState == 0 && current.gameState == 1)
    {
        print(String.Format("[FDNY] Menu→Gameplay | Map:'{0}' | RESET stage/IL split flag", vars.currentMap));
        vars.hasSplit = false;
        vars.lastMap = vars.currentMap;
    }
    
    // Reset stage-completion split flag when map changes DURING gameplay (multi-stage direct transitions)
    // This happens AFTER the split has been processed
    if (current.gameState == 1 && vars.hasSplit && vars.lastMap != "" && vars.lastMap != vars.currentMap)
    {
        print(String.Format("[FDNY] Map transition completed '{0}'→'{1}' | RESET stage/IL split flag, RESUME timer", 
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
        if (current.mapName == null)
            vars.currentMap = "";
        else
            vars.currentMap = current.mapName.ToLower().Trim();

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
    // Only split during gameplay and if we haven't already done the
    // stage/IL-ending split for this map.
    // Survivor subsplits do NOT set vars.hasSplit, so this still allows multiple
    // survivor subsplits before the final IL split.
    if (current.gameState != 1 || vars.hasSplit)
        return false;

    bool allowSurvivorSplits = vars.useSurvivorSplits;

    string map = vars.currentMap;

    bool isBank        = map.Contains("bank");
    bool isBar         = map.Contains("bar_r");
    bool isGasStation  = map.Contains("gas_r");
    bool isMilitary    = map.Contains("mbase");

    bool isSingleStageSurvivorMap =
        isBank || isBar || isGasStation || isMilitary;

    // ============================================================================
    // SURVIVOR SUBSPLITS (single-stage rescue maps only)
    // - Split on rescuedVictims increments, but ONLY if rescuedVictims < totalVictims
    //   → never splits on the final rescue
    // - Final IL split is always from the end-sound flag
    // - Does NOT touch vars.hasSplit (that is reserved for IL/stage completion)
    // ============================================================================
    if (allowSurvivorSplits && isSingleStageSurvivorMap)
    {
        // Basic sanity check: totalVictims > 0 and rescue count increased
        if (current.totalVictims > 0 && current.rescuedVictims > old.rescuedVictims)
        {
            // Never split when we've just rescued the FINAL survivor
            if (current.rescuedVictims < current.totalVictims)
            {
                // Example:
                //  - Military Base (5 total): splits at 1,2,3,4
                //  - Downtown Bar (6 total): splits at 1,2,3,4,5
                //  - Gas Station (7 total): splits at 1–6
                //  - Bank Robbery (6 total): splits at 1–5
                print(String.Format(
                    "[FDNY SPLIT] Survivor rescued | Map:'{0}' | Rescue:{1}/{2}",
                    map,
                    current.rescuedVictims,
                    current.totalVictims));

                // IMPORTANT: do NOT set vars.hasSplit here
                return true;
            }
            else
            {
                // This is the final survivor (rescuedVictims == totalVictims)
                // We intentionally do NOT split here. Final split will come from the
                // level-end sound, which avoids double-splits on Bank where the
                // 6th rescue can coincide with the exit trigger.
                print(String.Format(
                    "[FDNY] Final survivor rescued | Map:'{0}' | Rescue:{1}/{2} | Waiting for level-end sound",
                    map,
                    current.rescuedVictims,
                    current.totalVictims));
            }
        }
    }

    // ============================================================================
    // MAP TRANSITION SPLITS (Multi-stage levels)
    // ============================================================================    
    if (vars.lastMap.Contains("boat_a") && map.Contains("boat_b"))
    {
        print(String.Format("[FDNY SPLIT] Boat A→B | '{0}'→'{1}'", vars.lastMap, map));
        vars.hasSplit = true;
        return true;
    }
    
    if (vars.lastMap.Contains("subway_a") && map.Contains("subway_b"))
    {
        print(String.Format("[FDNY SPLIT] Subway A→B | '{0}'→'{1}'", vars.lastMap, map));
        vars.hasSplit = true;
        return true;
    }
    
    if (vars.lastMap.Contains("oil_rig_a") && map.Contains("oil_rig_b"))
    {
        print(String.Format("[FDNY SPLIT] Oil Rig A→B | '{0}'→'{1}'", vars.lastMap, map));
        vars.hasSplit = true;
        return true;
    }
    
    if (vars.lastMap.Contains("oil_rig_b") && map.Contains("oil_rig_c"))
    {
        print(String.Format("[FDNY SPLIT] Oil Rig B→C | '{0}'→'{1}'", vars.lastMap, map));
        vars.hasSplit = true;
        return true;
    }
    
    if (vars.lastMap.Contains("oil_rig_c") && map.Contains("oil_rig_d"))
    {
        print(String.Format("[FDNY SPLIT] Oil Rig C→D | '{0}'→'{1}'", vars.lastMap, map));
        vars.hasSplit = true;
        return true;
    }
    
    // ============================================================================
    // SINGLE-STAGE MAPS - Final IL splits via sound triggers
    // ============================================================================

    // Training level: no survivor logic, just final sound split
    if (map.Contains("training") && 
        old.trainingLevelEndSoundPlayed == 0 && current.trainingLevelEndSoundPlayed != 0)
    {
        print("[FDNY SPLIT] Training completed");
        vars.hasSplit = true;
        return true;
    }
    
    if (isBank && 
        old.bankLevelEndSoundPlayed == 0 && current.bankLevelEndSoundPlayed != 0)
    {
        print(String.Format(
            "[FDNY SPLIT] Bank completed | Final survivor:{0}/{1}",
            current.rescuedVictims,
            current.totalVictims));
        vars.hasSplit = true;
        return true;
    }
    
    if (isBar && 
        old.barLevelEndSoundPlayed == 0 && current.barLevelEndSoundPlayed != 0)
    {
        print(String.Format(
            "[FDNY SPLIT] Bar completed | Final survivor:{0}/{1}",
            current.rescuedVictims,
            current.totalVictims));
        vars.hasSplit = true;
        return true;
    }
    
    if (isGasStation && 
        old.gasStationLevelEndSoundPlayed == 0 && current.gasStationLevelEndSoundPlayed != 0)
    {
        print(String.Format(
            "[FDNY SPLIT] Gas Station completed | Final survivor:{0}/{1}",
            current.rescuedVictims,
            current.totalVictims));
        vars.hasSplit = true;
        return true;
    }
    
    if (isMilitary && 
        old.militaryBaseLevelEndSoundPlayed == 0 && current.militaryBaseLevelEndSoundPlayed != 0)
    {
        print(String.Format(
            "[FDNY SPLIT] Military Base completed | Final survivor:{0}/{1}",
            current.rescuedVictims,
            current.totalVictims));
        vars.hasSplit = true;
        return true;
    }
    
    // ============================================================================
    // MULTI-STAGE FINAL COMPLETIONS - Sound triggers
    // ============================================================================

    if (map.Contains("boat_b") && 
        old.boatLevelEndSoundPlayed == 0 && current.boatLevelEndSoundPlayed != 0)
    {
        print("[FDNY SPLIT] Boat B completed");
        vars.hasSplit = true;
        return true;
    }
    
    if (map.Contains("subway_b") && 
        old.subwayLevelEndSoundPlayed == 0 && current.subwayLevelEndSoundPlayed != 0)
    {
        print("[FDNY SPLIT] Subway B completed");
        vars.hasSplit = true;
        return true;
    }
    
    if (map.Contains("oil_rig_d") && 
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
    // Timer should pause:
    //  - After a stage/IL completion split (vars.hasSplit == true),
    //  - While in loading state (gameState == 2),
    //  - While in victory/end state (gameState == 3).
    //
    // Survivor subsplits do NOT touch vars.hasSplit, so they do NOT affect isLoading.
    return vars.hasSplit || current.gameState == 2 || current.gameState == 3;
}

reset
{
    // Manual reset only
    return false;
}
