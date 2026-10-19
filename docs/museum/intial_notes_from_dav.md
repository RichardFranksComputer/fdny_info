# Initial Notes from Dav

## Timer Differences

- nydesson uses IGT
- pauze's checks gamestate and includes newspaper at end
- RTA currently includes loading

## Goals

We need a LiveSplit timer that can reliably time records by the frame between:
- First frame of actionability within level
- Hitting end trigger

### Starting Timer
Starting timer will be more difficult. Options:
- Can I look for when the main game loop is active after a load?
- We can maybe use pauze's trigger for start, if this is difficult

## Level Triggers

- If there are exit and rescue triggers, exit trigger is the exit point
- Some levels only have exit triggers
- Bank has feedback loop where if you touch exit trigger before rescuing

### Boat Level
- Has multiple maps as one level
- 3 levels are segmented
  - Each of them has an end trigger, but not all of them call credits
  - Rescue triggers and end triggers are different

## Strings to Search For

### Level Start
```
level begins
Find and rescue the survivors!
```

### More Survivors Required
```
You can't leave now! There are still survivors in:
    boat
        cargo a
        engine room
```

## Rescuebot Names
- Blade Jackson
- Hotrod Stein
- Spitfire Li
- Smockestack Williams
- Brushfire Miller

## Other Notes
- F8 (unknown context)
- Survivor subsplits for ILs


