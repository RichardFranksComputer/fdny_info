state("FDNYFirefighter")
{
	byte ScreenState: "Genesis.dll", 0x38A7B4;
}

startup
{
	settings.Add("DGVoodoo");
	settings.SetToolTip("DGVoodoo", "Check if you are running with DGVoodoo");	
	settings.Add("Rescue Subsplits");
	settings.SetToolTip("Rescue Subsplits", "TODO: Check if you are running subsplits for survivors rescued");
}

start
{
	if(settings["DGVoodoo"]) {
		if(current.ScreenState == 21 && old.ScreenState == 200){
			return true;
		}
	}
}

split 
{	
	if(settings["Rescue Subsplits"]) {
		if(settings["DGVoodoo"]) {
			if(current.Survivors > old.Survivors) {
				return true;
			}
		}
	} else {
		if(settings["DGVoodoo"]) {
			if(current.ScreenState == 180 && old.ScreenState == 21) {
				return true;
			}
		}
	}
}

isLoading 
{
	if(settings["DGVoodoo"]) {
	return (current.ScreenState == 0 || 
			current.ScreenState == 7 || 
			current.ScreenState == 200 || 
			current.ScreenState == 180 ||
			current.ScreenState == 192 ||
			current.ScreenState == 208 ||
			current.ScreenState == 68); 
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