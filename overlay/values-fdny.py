"""What the overlay shows for FDNYFirefighter.exe: WATCHES (raw reads +
calculated placeholders) and the compute() logic behind them. Autoloaded
by watch_engine.py via the values-*.py naming convention - copy this file
to add a new game."""

import math

PROCESS_NAME = "FDNYFirefighter.exe"

# Modules referenced below, named once so there's a single spot to edit if
# either ever changes.
FDNY = "FDNYFirefighter.exe"
GENESIS = "genesis.dll"

def watch(label, module, base, offsets=(), type="float", feeds=None):
    """One raw memory read, shown as `label`. `feeds`, if given, is the role
    name compute() reads this value back under (see the `feeds` dict it
    receives) - leave it out if nothing else needs this value."""
    return {"label": label, "module": module, "base": base,
            "offsets": list(offsets), "type": type, "feeds": feeds}

def calculated(label, kind):
    """One value produced by compute() below, shown as `label` under the
    key `kind` (must match a key compute() actually returns)."""
    return {"label": label, "calculated": kind}

# One entry per line shown in the overlay, in list order. Reverse-engineered
# data - a wrong address just shows "<read?>"/"<ptr?>", nothing else breaks.

WATCHES = [
    calculated("XY Speed", "speed"),
    watch("Vel X", FDNY, 0x00103A78, offsets=(0x30, 0x104), feeds="velocity_x"),
    watch("Vel Y", FDNY, 0x00103A78, offsets=(0x30, 0xFC), feeds="velocity_y"),
    watch("Vel Z", FDNY, 0x00103A78, offsets=(0x30, 0x100), feeds="velocity_z"),
    watch("Player State", FDNY, 0x00103A78, offsets=(0x30, 0x18c), type="byte", feeds="player_state"),
    watch("Player Ground State", FDNY, 0x00103A78, offsets=(0x30, 0x12c), type="byte"),
    watch("Z Coll Center", GENESIS, 0x362EE8, feeds="z_collision_center"),
    watch("Z Ground Height", FDNY, 0x00103A78, offsets=(0x30, 0x3404), feeds="z_ground_height"),
    calculated("Last Jump", "previous_jump"),
    calculated("Best Jump", "previous_jump_max"),
    calculated("Last Best Jump", "current_jump_max"),
]

# -----------------------------------------------------------------------
# Calculated values
# -----------------------------------------------------------------------

PLAYER_STATE_ON_LADDER = 5


def make_state():
    """Fresh persistent state for a new process attach."""
    return {
        "current_height_in_jump": 0.0,
        "previous_jump": 0.0,
        "previous_jump_max": 0.0,  # 2nd-best jump of all time
        "current_jump_max": 0.0,  # best jump of all time
        "jump_baseline": None,  # standing height at start of jump
        "pending_ladder_rebaseline": False,  # see _update_jump_height
    }


def compute(feeds, state):
    """Called once per tick with the latest raw reads (`feeds`) and this
    game's persistent `state` (mutated in place). Returns {calculated key:
    value}; None means "not available yet" (rendered as "<wait>")."""
    out = {}

    out["speed"] = _speed(feeds)

    _update_jump_height(feeds, state)
    out["previous_jump"] = state["previous_jump"]
    out["previous_jump_max"] = state["previous_jump_max"]
    out["current_jump_max"] = state["current_jump_max"]

    return out


def _speed(feeds):
    """Vel X/Y magnitude, or None until both are available."""
    vx, vy = feeds.get("velocity_x"), feeds.get("velocity_y")
    if vx is None or vy is None:
        return None
    return math.sqrt(vx**2 + vy**2)  # shout out to nyddesson for the original idea on this


def _update_jump_height(feeds, state):
    """Tracks jump height from Z Collision Center vs Z Ground Height;
    skipped while on a ladder (state 5), which moves Z the same way a jump
    does. Rebaselines on the next reading after leaving one, since state
    doesn't reliably hold 5 for the whole climb."""
    if feeds.get("player_state") == PLAYER_STATE_ON_LADDER:
        state["pending_ladder_rebaseline"] = True
        return

    z_collision_center = feeds.get("z_collision_center")
    z_ground_height = feeds.get("z_ground_height")
    if z_collision_center is None or z_ground_height is None:
        return

    current_height = z_collision_center - z_ground_height
    if current_height < 50:  # crouched - not a usable baseline
        return

    if state["jump_baseline"] is None or state["pending_ladder_rebaseline"]:
        state["pending_ladder_rebaseline"] = False
        state["jump_baseline"] = current_height
        state["current_height_in_jump"] = 0.0
        return

    relative_height = current_height - state["jump_baseline"]

    if abs(relative_height) < 5:  # landed
        if state["current_height_in_jump"] > 0:
            completed = state["current_height_in_jump"]
            state["previous_jump"] = completed
            if completed > state["current_jump_max"]:
                state["previous_jump_max"] = state["current_jump_max"]
                state["current_jump_max"] = completed
            elif completed > state["previous_jump_max"]:
                state["previous_jump_max"] = completed
            state["current_height_in_jump"] = 0.0
        state["jump_baseline"] = current_height
        return

    state["current_height_in_jump"] = max(state["current_height_in_jump"], relative_height)
