"""NPC hallway movement: leaving/returning to post, calling NPCs back,
wandering, goal-driven room visits, and hallway-passing detection.

Department-head NPCs (Captain, Head of Personnel, Security Guard, Doctor,
Engineer, Botanist, Bartender) are each tied to a "post" - the special room
for their job. They can randomly leave that post, then choose to wander the
hallway, beeline to another room (stay 2 ticks, then return home), or head
straight back to their station. Staff Assistants have no post; they wander
or visit rooms, then resume wandering.
"""

import random
from collections import deque

from space_online.game.maps import donut

# Job -> the donut room key that job's NPC is posted at.
JOB_POST_KEY = {
    "Captain": donut.BRIDGE_KEY,
    "Head of Personnel": donut.BRIDGE_KEY,
    "Security Guard": donut.SECURITY_KEY,
    "Doctor": donut.MEDBAY_KEY,
    "Engineer": donut.ENGINEERING_KEY,
    "Botanist": donut.BOTANY_KEY,
    "Bartender": donut.BAR_KEY,
}

NPC_LEAVE_POST_CHANCE = 0.20
# Captain and Security Guard patrol more often (~25% higher leave chance).
PATROL_LEAVE_POST_CHANCE = 0.25
PATROL_JOBS = frozenset({"Captain", "Security Guard"})
NPC_CALL_SUCCESS_CHANCE = 0.75
NPC_AUTO_RETURN_CHANCE = 0.15
STAFF_ROOM_VISIT_CHANCE = 0.25
ROOM_VISIT_TICKS = 2
NPC_EVENT_CHANCE = 0.15

# Off-duty posted NPC three-way weights (sum to 1.0).
GOAL_WEIGHT_RETURN = NPC_AUTO_RETURN_CHANCE  # 0.15
GOAL_WEIGHT_ROOM = STAFF_ROOM_VISIT_CHANCE  # 0.25
GOAL_WEIGHT_WANDER = 1.0 - GOAL_WEIGHT_RETURN - GOAL_WEIGHT_ROOM  # 0.60

# Rooms NPCs may visit (not Quarters).
VISITABLE_ROOM_KEYS = tuple(
    key for key in donut.SPECIAL_ROOM_HALLWAY if key != donut.QUARTERS_KEY
)


def leave_post_chance_for(npc):
    """Return the per-round chance that this on-duty NPC leaves their post."""
    if npc.get("job") in PATROL_JOBS:
        return PATROL_LEAVE_POST_CHANCE
    return NPC_LEAVE_POST_CHANCE


# --- Lookups -----------------------------------------------------------

def has_post(npc):
    """Return True if this NPC's job is tied to a station post/room."""
    return npc.get("job") in JOB_POST_KEY


def post_key_for_job(job):
    """Return the donut room key for a job's post, or None if it has no post."""
    return JOB_POST_KEY.get(job)


def npcs_for_job(station_crew, job_name):
    """Return every NPC currently holding job_name."""
    return [npc for npc in station_crew if npc.get("job") == job_name]


def on_duty_npc_for_job(station_crew, job_name):
    """Return the first NPC holding job_name who is currently on duty, or None."""
    for npc in npcs_for_job(station_crew, job_name):
        if npc.get("in_jail", False):
            continue
        if npc.get("on_duty", True):
            return npc
    return None


def any_npc_for_job(station_crew, job_name):
    """Return the first NPC holding job_name regardless of duty status, or None."""
    npcs = npcs_for_job(station_crew, job_name)
    return npcs[0] if npcs else None


# --- Location helpers ----------------------------------------------------

def _location_dict_from_key(key):
    x_str, y_str = key.split(",")
    return {"x": int(x_str), "y": int(y_str)}


def location_for_post(job):
    """Return the {'x','y'} location dict for a job's post, or None."""
    post_key = post_key_for_job(job)
    if post_key is None:
        return None
    return _location_dict_from_key(post_key)


def _hallway_tile_for_post(post_key):
    return donut.SPECIAL_ROOM_HALLWAY.get(post_key)


def _is_hallway_location(location):
    if not isinstance(location, dict) or "x" not in location or "y" not in location:
        return False
    key = f"{location.get('x')},{location.get('y')}"
    return key in donut.SHIP_MAP and key not in donut.SPECIAL_ROOM_TILES


def _is_inside_special_room(location):
    if not isinstance(location, dict) or "x" not in location or "y" not in location:
        return False
    key = f"{location.get('x')},{location.get('y')}"
    return key in donut.SPECIAL_ROOM_TILES


def pick_random_hallway_location():
    """Return a random {'x','y'} location on a plain hallway tile (no special rooms)."""
    hallway_keys = [key for key in donut.SHIP_MAP if key not in donut.SPECIAL_ROOM_TILES]
    key = random.choice(hallway_keys)
    return _location_dict_from_key(key)


def _clear_npc_goal(npc):
    npc["npc_goal"] = None
    npc["npc_goal_room_key"] = None


# --- Goal selection --------------------------------------------------------

def _pick_visit_room_key(npc):
    """Choose a visitable room other than this NPC's own post."""
    own_post = post_key_for_job(npc.get("job")) if has_post(npc) else None
    choices = [key for key in VISITABLE_ROOM_KEYS if key != own_post]
    if not choices:
        choices = list(VISITABLE_ROOM_KEYS)
    return random.choice(choices)


def _pick_posted_npc_goal(npc):
    """Three-way roll: wander / visit room / return to station."""
    roll = random.random()
    if roll < GOAL_WEIGHT_RETURN:
        npc["npc_goal"] = "return_to_post"
        npc["npc_goal_room_key"] = None
    elif roll < GOAL_WEIGHT_RETURN + GOAL_WEIGHT_ROOM:
        npc["npc_goal"] = "visit_room"
        npc["npc_goal_room_key"] = _pick_visit_room_key(npc)
    else:
        npc["npc_goal"] = "wander"
        npc["npc_goal_room_key"] = None


def _pick_staff_assistant_goal(npc):
    """Two-way roll: visit room (0.25) or wander (0.75)."""
    if random.random() < STAFF_ROOM_VISIT_CHANCE:
        npc["npc_goal"] = "visit_room"
        npc["npc_goal_room_key"] = _pick_visit_room_key(npc)
    else:
        npc["npc_goal"] = "wander"
        npc["npc_goal_room_key"] = None


# --- Leaving post ----------------------------------------------------------

def _send_npc_wandering(npc):
    """Mark a posted NPC as off duty, place them outside their door, pick a goal."""
    npc["on_duty"] = False
    post_key = post_key_for_job(npc.get("job"))
    hallway_tile = _hallway_tile_for_post(post_key) if post_key else None
    if hallway_tile:
        npc["location"] = {"x": hallway_tile[0], "y": hallway_tile[1]}
    else:
        npc["location"] = pick_random_hallway_location()
    npc["room_visit_remaining"] = 0
    _pick_posted_npc_goal(npc)


def roll_departures(station_crew):
    """Randomly send on-duty posted NPCs away from their post."""
    for npc in station_crew:
        if npc.get("in_jail", False):
            continue
        if not has_post(npc):
            continue
        if not npc.get("on_duty", True):
            continue
        if random.random() < leave_post_chance_for(npc):
            _send_npc_wandering(npc)


# --- Returning to post -----------------------------------------------------

def _return_to_post(npc):
    npc["on_duty"] = True
    location = location_for_post(npc.get("job"))
    if location is not None:
        npc["location"] = location
    npc["room_visit_remaining"] = 0
    _clear_npc_goal(npc)


def call_npc(npc, elapsed_seconds=0.0):
    """Attempt to call an off-duty NPC back to their post.

    ``elapsed_seconds`` is the current master game clock value, used to
    compute the jail countdown if the NPC happens to be locked up.
    Returns (success, message).
    """
    name = npc.get("name", "They")
    if npc.get("in_jail", False):
        from space_online.game.helper_methods.jail import format_jail_time, jail_seconds_remaining

        remaining = format_jail_time(jail_seconds_remaining(npc, elapsed_seconds))
        return False, f"{name} is in jail and will be released in {remaining}."

    if npc.get("on_duty", True):
        return True, f"{name} is already at their post."

    if random.random() < NPC_CALL_SUCCESS_CHANCE:
        _return_to_post(npc)
        return True, f"{name} answers the call and heads back to their post."

    return False, f"{name} doesn't answer. Maybe try calling again later."


def reassign_npc_post(npc, new_job):
    """Move an NPC to their new job's post right after their job changes.

    Call this after mutating npc["job"] = new_job. If the new job has a post,
    the NPC immediately reports there (on duty), even if they were away from
    their old post. If the new job has no post (e.g. Staff Assistant), they
    become a wanderer instead.
    """
    location = location_for_post(new_job)
    if location is not None:
        npc["on_duty"] = True
        npc["location"] = location
        npc["room_visit_remaining"] = 0
        _clear_npc_goal(npc)
    else:
        npc.pop("on_duty", None)
        npc["room_visit_remaining"] = 0
        npc["location"] = pick_random_hallway_location()
        _pick_staff_assistant_goal(npc)


# --- Pathfinding / beeline -------------------------------------------------

def _hallway_neighbor_tiles(x, y, ship_map):
    """Return adjacent hallway tiles reachable from (x, y)."""
    directions = donut.get_available_directions(x, y)
    neighbors = []
    for direction, ok in directions.items():
        if not ok:
            continue
        nx, ny = x, y
        if direction == "north":
            nx += 1
        elif direction == "south":
            nx -= 1
        elif direction == "east":
            ny += 1
        elif direction == "west":
            ny -= 1
        key = f"{nx},{ny}"
        if key in ship_map and key not in donut.SPECIAL_ROOM_TILES:
            neighbors.append((nx, ny))
    return neighbors


def _beeline_one_step(npc, target_xy, ship_map):
    """Move one hallway step toward target_xy. Returns True if already there."""
    location = npc.get("location") or {}
    if _is_inside_special_room(location):
        room_key = f"{location.get('x')},{location.get('y')}"
        hallway_tile = donut.SPECIAL_ROOM_HALLWAY.get(room_key)
        if hallway_tile:
            npc["location"] = {"x": hallway_tile[0], "y": hallway_tile[1]}
        else:
            npc["location"] = pick_random_hallway_location()
        location = npc["location"]

    if not _is_hallway_location(location):
        npc["location"] = pick_random_hallway_location()
        location = npc["location"]

    start = (location["x"], location["y"])
    target = (int(target_xy[0]), int(target_xy[1]))
    if start == target:
        return True

    # BFS for shortest path; store parent pointers to reconstruct first step.
    queue = deque([start])
    parents = {start: None}
    found = False
    while queue:
        current = queue.popleft()
        if current == target:
            found = True
            break
        for neighbor in _hallway_neighbor_tiles(current[0], current[1], ship_map):
            if neighbor not in parents:
                parents[neighbor] = current
                queue.append(neighbor)

    if not found:
        _wander_one_step(npc, ship_map)
        return False

    # Walk back from target to find the step after start.
    step = target
    while parents[step] is not None and parents[step] != start:
        step = parents[step]
    npc["location"] = {"x": step[0], "y": step[1]}
    return step == target


# --- Wandering ---------------------------------------------------------

def _wander_one_step(npc, ship_map):
    """Move a wandering NPC one random valid step along the hallway ring."""
    location = npc.get("location")
    if not _is_hallway_location(location) or f"{location.get('x')},{location.get('y')}" not in ship_map:
        npc["location"] = pick_random_hallway_location()
        return

    x, y = location["x"], location["y"]
    directions = donut.get_available_directions(x, y)
    available = [direction for direction, ok in directions.items() if ok]
    if not available:
        return

    direction = random.choice(available)
    if direction == "north":
        x += 1
    elif direction == "south":
        x -= 1
    elif direction == "east":
        y += 1
    elif direction == "west":
        y -= 1

    key = f"{x},{y}"
    if key not in ship_map:
        return

    npc["location"] = {"x": x, "y": y}


def _apply_silent_npc_event(npc):
    """Apply a minor, silent stat change to a wandering NPC (no popup/log)."""
    limbs = npc.get("limbs")
    if not limbs:
        return

    outcome = random.choice(["minor_injury", "minor_heal", "nothing"])
    if outcome == "minor_injury":
        limb = random.choice(list(limbs.keys()))
        damage = random.randint(2, 8)
        limbs[limb] = max(0, limbs[limb] - damage)
    elif outcome == "minor_heal":
        injured = [limb for limb, health in limbs.items() if health < 100]
        if injured:
            limb = random.choice(injured)
            heal = random.randint(2, 8)
            limbs[limb] = min(100, limbs[limb] + heal)


def _maybe_trigger_silent_event(npc):
    if random.random() < NPC_EVENT_CHANCE:
        _apply_silent_npc_event(npc)


def _enter_room(npc, room_key, game=None, player_data=None, station_crew=None):
    npc["location"] = _location_dict_from_key(room_key)
    npc["room_visit_remaining"] = ROOM_VISIT_TICKS

    # Security Guards check warrants when they enter a room.
    if npc.get("job") == "Security Guard" and station_crew is not None:
        from space_online.game.helper_methods.game_clock import get_elapsed_seconds
        from space_online.game.helper_methods.jail import (
            arrest_wanted_in_room,
            has_fine,
            is_jailed,
            member_location_key,
            resolve_fine_with_guard,
        )

        elapsed_seconds = get_elapsed_seconds(player_data) if player_data else 0.0

        if (
            player_data
            and has_fine(player_data)
            and not is_jailed(player_data)
            and member_location_key(player_data) == room_key
        ):
            resolve_fine_with_guard(
                player_data,
                game=game,
                is_player=True,
                guard_name=npc.get("name", "A security guard"),
                elapsed_seconds=elapsed_seconds,
            )

        for other in list(station_crew):
            if other is npc:
                continue
            if (
                has_fine(other)
                and not is_jailed(other)
                and member_location_key(other) == room_key
            ):
                resolve_fine_with_guard(
                    other,
                    game=game,
                    is_player=False,
                    guard_name=npc.get("name", "A security guard"),
                    elapsed_seconds=elapsed_seconds,
                )

        arrest_wanted_in_room(
            room_key,
            player_data or {},
            station_crew,
            game=game,
            guard=npc,
            elapsed_seconds=elapsed_seconds,
        )


def _exit_visited_room_to_hallway(npc):
    """Place the NPC on the hallway tile outside their current room."""
    location = npc.get("location") or {}
    room_key = f"{location.get('x')},{location.get('y')}"
    hallway_tile = donut.SPECIAL_ROOM_HALLWAY.get(room_key)
    if hallway_tile:
        npc["location"] = {"x": hallway_tile[0], "y": hallway_tile[1]}
    else:
        npc["location"] = pick_random_hallway_location()
    npc["room_visit_remaining"] = 0


def _tick_room_visit_then_return_home(npc):
    """Countdown an in-room visit; when done, exit hall and set return-to-post."""
    remaining = npc.get("room_visit_remaining", 0)
    if remaining <= 0:
        return False
    npc["room_visit_remaining"] = remaining - 1
    if npc["room_visit_remaining"] <= 0:
        _exit_visited_room_to_hallway(npc)
        npc["npc_goal"] = "return_to_post"
        npc["npc_goal_room_key"] = None
    return True


def _tick_room_visit_then_wander(npc):
    """Countdown an in-room visit for staff; when done, exit and clear goal."""
    remaining = npc.get("room_visit_remaining", 0)
    if remaining <= 0:
        return False
    npc["room_visit_remaining"] = remaining - 1
    if npc["room_visit_remaining"] <= 0:
        _exit_visited_room_to_hallway(npc)
        _clear_npc_goal(npc)
    return True


def _pursue_visit_room(npc, ship_map, game=None, player_data=None, station_crew=None):
    """Beeline to goal room; enter when at the door."""
    room_key = npc.get("npc_goal_room_key")
    if not room_key:
        npc["npc_goal"] = "wander"
        return

    location = npc.get("location") or {}
    current_key = f"{location.get('x')},{location.get('y')}"
    if current_key == room_key and npc.get("room_visit_remaining", 0) > 0:
        return

    hallway_tile = donut.SPECIAL_ROOM_HALLWAY.get(room_key)
    if not hallway_tile:
        npc["npc_goal"] = "wander"
        return

    arrived = _beeline_one_step(npc, hallway_tile, ship_map)
    if arrived:
        _enter_room(npc, room_key, game=game, player_data=player_data, station_crew=station_crew)


def _pursue_return_to_post(npc, ship_map):
    """Beeline to post hallway door, then clock in on duty."""
    post_key = post_key_for_job(npc.get("job"))
    hallway_tile = _hallway_tile_for_post(post_key) if post_key else None
    if not hallway_tile:
        _return_to_post(npc)
        return

    arrived = _beeline_one_step(npc, hallway_tile, ship_map)
    if arrived:
        _return_to_post(npc)


def _step_off_duty_npc(npc, ship_map, game=None, player_data=None, station_crew=None):
    """Advance a wandering (off-duty) posted NPC by one round."""
    goal = npc.get("npc_goal")

    # Inside a visit: count down, then head home.
    location = npc.get("location") or {}
    current_key = f"{location.get('x')},{location.get('y')}"
    if (
        goal == "visit_room"
        and npc.get("room_visit_remaining", 0) > 0
        and current_key == npc.get("npc_goal_room_key")
    ):
        _tick_room_visit_then_return_home(npc)
        return

    if goal == "visit_room":
        _pursue_visit_room(
            npc, ship_map, game=game, player_data=player_data, station_crew=station_crew
        )
        return

    if goal == "return_to_post":
        _pursue_return_to_post(npc, ship_map)
        return

    # Wander (or missing goal): one random step, then re-roll next goal.
    if not goal:
        _pick_posted_npc_goal(npc)
        goal = npc.get("npc_goal")
        if goal == "visit_room":
            _pursue_visit_room(
                npc, ship_map, game=game, player_data=player_data, station_crew=station_crew
            )
            return
        if goal == "return_to_post":
            _pursue_return_to_post(npc, ship_map)
            return

    _wander_one_step(npc, ship_map)
    _maybe_trigger_silent_event(npc)
    _pick_posted_npc_goal(npc)


def _step_staff_assistant(npc, ship_map, game=None, player_data=None, station_crew=None):
    """Advance a Staff Assistant by one round (wander or visit room)."""
    goal = npc.get("npc_goal")
    location = npc.get("location") or {}
    current_key = f"{location.get('x')},{location.get('y')}"

    if (
        goal == "visit_room"
        and npc.get("room_visit_remaining", 0) > 0
        and current_key == npc.get("npc_goal_room_key")
    ):
        _tick_room_visit_then_wander(npc)
        return

    if goal == "visit_room":
        _pursue_visit_room(
            npc, ship_map, game=game, player_data=player_data, station_crew=station_crew
        )
        return

    if not goal:
        _pick_staff_assistant_goal(npc)
        goal = npc.get("npc_goal")
        if goal == "visit_room":
            _pursue_visit_room(
                npc, ship_map, game=game, player_data=player_data, station_crew=station_crew
            )
            return

    _wander_one_step(npc, ship_map)
    _maybe_trigger_silent_event(npc)
    _pick_staff_assistant_goal(npc)


def step_wanderers(station_crew, ship_map, game=None, player_data=None):
    """Advance every wandering NPC (off-duty posted NPCs + Staff Assistants)."""
    for npc in station_crew:
        if npc.get("in_jail", False):
            continue
        if has_post(npc):
            if npc.get("on_duty", True):
                continue
            _step_off_duty_npc(
                npc, ship_map, game=game, player_data=player_data, station_crew=station_crew
            )
        else:
            _step_staff_assistant(
                npc, ship_map, game=game, player_data=player_data, station_crew=station_crew
            )


# --- Hallway encounters ----------------------------------------------------

def find_hall_passersby(player_data, station_crew):
    """Return wandering NPCs whose location matches the player's current tile."""
    location = player_data.get("location") or {}
    player_tile = (location.get("x"), location.get("y"))

    passersby = []
    for npc in station_crew:
        if npc.get("in_jail", False):
            continue
        if has_post(npc) and npc.get("on_duty", True):
            continue
        if npc.get("room_visit_remaining", 0) > 0:
            continue

        npc_location = npc.get("location") or {}
        npc_tile = (npc_location.get("x"), npc_location.get("y"))
        if npc_tile == player_tile:
            passersby.append(npc)

    return passersby
