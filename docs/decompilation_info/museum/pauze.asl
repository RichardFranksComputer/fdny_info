state("FDNYFirefighter")
{
	byte ScreenState: "Genesis.dll", 0x38A7B4;
	float gameTimer: 0x102AAC, 0x3B0, 0x0, 0x10, 0x88, 0x0, 0xA8;
}

startup
{
	settings.Add("DxWnd");
	settings.Add("DGVoodoo");
	settings.SetToolTip("DxWnd", "Check if you are running with DxWnd (counts if running with DGVoodoo too)");
	settings.SetToolTip("DGVoodoo", "Check if you are running with DGVoodoo (counts if running with DxWnd too)");
}

start
{
  if(settings["DxWnd"] && settings["DGVoodoo"]){
    if(current.ScreenState == 22 && old.ScreenState == 6){
		  return true;
	  } else if(current.ScreenState == 12 && old.ScreenState == 6) {
		  return true;
	  }
  } else if(settings["DGVoodoo"]) {
    if(current.ScreenState == 21 && old.ScreenState == 200){
		  return true;
	}
  }
}

update 
{
	//setGameTime(TimeSpan.FromSeconds(current.gameTimer));
	print(current.gameTimer.ToString());
}

split 
{
  if(settings["DxWnd"] && settings["DGVoodoo"]) {
	  if(current.ScreenState == 5 && old.ScreenState == 22) {
		  return true;
	  } else if(current.ScreenState == 5 && old.ScreenState == 12) {
		  return true;
	  } else if(current.ScreenState == 1 && old.ScreenState == 22) {
		  return true;
	  } else if(current.ScreenState == 1 && old.ScreenState == 12) {
		  return true;
	  }
  } else if(settings["DGVoodoo"]) {
    if(current.ScreenState == 180 && old.ScreenState == 21) {
		  return true;
	}
  }
}

isLoading 
{

  if(settings["DxWnd"] && settings["DGVoodoo"]) {
	  return (current.ScreenState == 6 || 
			current.ScreenState == 56 || 
			current.ScreenState == 61 || 
			current.ScreenState == 1 || 
			current.ScreenState == 5);	
  } else if(settings["DGVoodoo"]) {
	return (current.ScreenState == 0 || 
			current.ScreenState == 7 || 
			current.ScreenState == 200 || 
			current.ScreenState == 180 ||
			current.ScreenState == 72 ||
			current.ScreenState == 68); 
  }
}

gameTime
{
	if(TimeSpan.FromSeconds(current.gameTimer / 1000) > TimeSpan.FromSeconds(old.gameTimer / 1000)){
	return TimeSpan.FromSeconds((current.gameTimer / 1000) - 2);
	}
}

// DxWnd with DGVoodoo

// Main menu and Result Screen (Hose): 1
// Career: 56
// Briefing: 6
// Scores and Result Screen (Rescue): 5
// Options: 61
// Gameplay (Rescue): 22
// Gameplay (Hose and Rescue or Vision Goggles): 12
// Gameplay (Rescue Alert + Gogglees): 190
// Gameplay (Holding survivor + Goggles): 172

// DGVoodoo

// Main menu: 236
// Main menu with option hovered: 228
// Career: 248
// Briefing: 239
// Scores and Result Screen (Rescue): 236
// Options: 1
// Gameplay (Rescue): 240
// Gameplay (Hose): 224
// Gameplay (Rescue with Vision Goggles): 225
// Gameplay (Rescue Alert + Gogglees): 152
// Gameplay (Holding survivor + Goggles): 138

// DGVoodoo v2

// Main menu: 0
// Options and Career: 7
// Briefing: 200
// Scores: 68
// Gameplay (Rescue): 21
// Result (Loading): 180
// Result (Complete): 72