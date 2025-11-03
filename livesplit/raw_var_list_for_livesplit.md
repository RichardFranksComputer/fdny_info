// this should be all values needed to make a livesplit
// map splits to use if/then for "if map name is x, split when sound value is non-zero
// subplits may be possible for map stages and victim counts for each
//
// note that *LevelEndSoundPlayed values may become nonzero on levels where they are not used to determine completion
// for instance, barLevelEndSoundPlayed may be nonzero on boat map
//
// gameState is 2 on map load, 3 on victory, but state transitions can be too fast for livesplit to monitor

gameState, int gameState : 0x00102AAC, 0x6F0; // 0 = menu, 1 = in game.
mapName, string10 mapName : 0x00102AAC, 0x688, 0x0, 0xC;
totalVictims, int totalVictims : 0x00103A78, 0x30, 0x3528;
rescuedVictims, int rescuedVictims : 0x00103A78, 0x30, 0x352C;

bank, int bankLevelEndSoundPlayed : 0x00103A78, 0x8, 0x0, 0x158, 0x0;
bar_r, int barLevelEndSoundPlayed : 0x00103A78, 0x8, 0x0, 0xFC, 0x0;
boat_b, int boatLevelEndSoundPlayed : 0x00103A78, 0x8, 0x0, 0xBC, 0x0;
gas_r, int gasStationLevelEndSoundPlayed : 0x00103A78, 0x8, 0x0, 0xF0, 0x0;
mbase, int militaryBaseLevelEndSoundPlayed : 0x00103A78, 0x8, 0x0, 0xC8, 0x0;
oil_rig_d, int oilRigDLevelEndSoundPlayed : 0x00103A78, 0x8, 0x0, 0xC4, 0x0;
subway_b, int subwayLevelEndSoundPlayed : 0x00103A78, 0x8, 0x0, 0x144, 0x0;
training, int trainingLevelEndSoundPlayed : 0x00103A78, 0x8, 0x0, 0x104, 0x0;