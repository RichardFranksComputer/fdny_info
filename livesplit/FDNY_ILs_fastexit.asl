state("FDNYFirefighter")
{
    int gameState : 0x00102AAC, 0x6F0;
    string10 mapName : 0x00102AAC, 0x688, 0x0, 0xC;
    int totalVictims : 0x00103A78, 0x30, 0x3528;
    int rescuedVictims : 0x00103A78, 0x30, 0x352C;

    int bankLevelEndSoundPlayed : 0x00103A78, 0x8, 0x0, 0x158, 0x0;
    int barLevelEndSoundPlayed : 0x00103A78, 0x8, 0x0, 0xFC, 0x0;
    int gasStationLevelEndSoundPlayed : 0x00103A78, 0x8, 0x0, 0xF0, 0x0;
    int militaryBaseLevelEndSoundPlayed : 0x00103A78, 0x8, 0x0, 0xC8, 0x0;
    int trainingLevelEndSoundPlayed : 0x00103A78, 0x8, 0x0, 0x104, 0x0;

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

    if (vars.frameCount % 300 == 0)
    {
        print(String.Format("[FDNY] Frame:{0} | State:{1} | Map:'{2}' | Split:{3} | LastMap:'{4}'",
            vars.frameCount,
            current.gameState,
            vars.currentMap,
            vars.hasSplit,
            vars.lastMap));
    }

    if (old.gameState == 0 && current.gameState == 1)
    {
        print(String.Format("[FDNY] Menu→Gameplay | Map:'{0}' | RESET split flag", vars.currentMap));
        vars.hasSplit = false;
        vars.lastMap = vars.currentMap;
    }

    if (current.gameState == 1 && vars.hasSplit && vars.lastMap != vars.currentMap)
    {
        print(String.Format("[FDNY] Map transition completed '{0}'→'{1}' | RESET split flag, RESUME timer", 
            vars.lastMap, vars.currentMap));
        vars.hasSplit = false;
        vars.lastMap = vars.currentMap;
    }
}

start
{
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
    if (current.gameState != 1 || vars.hasSplit)
        return false;

    string[,] transitions = {
        { "boat_a", "boat_b" },
        { "subway_a", "subway_b" },
        { "oil_rig_a", "oil_rig_b" },
        { "oil_rig_b", "oil_rig_c" },
        { "oil_rig_c", "oil_rig_d" }
    };

    for (int i = 0; i < transitions.GetLength(0); i++)
    {
        if (vars.lastMap.Contains(transitions[i,0]) && vars.currentMap.Contains(transitions[i,1]))
        {
            print(String.Format("[FDNY SPLIT] {0}→{1} | '{2}'→'{3}'", transitions[i,0], transitions[i,1], vars.lastMap, vars.currentMap));
            vars.hasSplit = true;
            return true;
        }
    }

    var sounds = new (string keyword, int oldVal, int currVal, string label)[] {
        ("training", old.trainingLevelEndSoundPlayed, current.trainingLevelEndSoundPlayed, "Training"),
        ("bank", old.bankLevelEndSoundPlayed, current.bankLevelEndSoundPlayed, "Bank"),
        ("bar_r", old.barLevelEndSoundPlayed, current.barLevelEndSoundPlayed, "Bar"),
        ("gas_r", old.gasStationLevelEndSoundPlayed, current.gasStationLevelEndSoundPlayed, "Gas Station"),
        ("mbase", old.militaryBaseLevelEndSoundPlayed, current.militaryBaseLevelEndSoundPlayed, "Military Base"),
        ("boat_b", old.boatLevelEndSoundPlayed, current.boatLevelEndSoundPlayed, "Boat B"),
        ("subway_b", old.subwayLevelEndSoundPlayed, current.subwayLevelEndSoundPlayed, "Subway B"),
        ("oil_rig_d", old.oilRigDLevelEndSoundPlayed, current.oilRigDLevelEndSoundPlayed, "Oil Rig D")
    };

    foreach (var s in sounds)
    {
        if (vars.currentMap.Contains(s.keyword) && s.oldVal == 0 && s.currVal != 0)
        {
            print(String.Format("[FDNY SPLIT] {0} completed", s.label));
            vars.hasSplit = true;
            return true;
        }
    }

    return false;
}

isLoading
{
    return vars.hasSplit || current.gameState == 2 || current.gameState == 3;
}

reset
{
    TimeSpan elapsed = timer.CurrentTime.RealTime.GetValueOrDefault();
    if (current.gameState == 0)
    {
        print("[FDNY RESET] ✓ Returned to menu");
        return true;
    }
    if (vars.lastMap != vars.currentMap && elapsed < TimeSpan.FromSeconds(20))
    {
        print("[FDNY RESET] Early map switch detected < 20s");
        return true;
    }
    return false;
}
