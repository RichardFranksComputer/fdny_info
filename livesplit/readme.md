load all_values_for_livesplit.ct into cheatengine to verify all variables

the level end trigger is hooked to a sound channel whose value is 0 until the level ends, then it becomes nonzero

it only works for rescue levels

other sound pointers can be found using the method described in [find_sound_pointer.md](find_sound_pointer.md)

the goal is to have livesplit look for "when this isn't 0, stop timing"