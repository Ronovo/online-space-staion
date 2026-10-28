"""Universal master game clock.

Every timed system in the game (power, oxygen, alcohol, jail, the stock
market, NPC wandering) reads its "now" from a single elapsed-seconds
counter here instead of calling ``datetime.now()`` independently. The
counter starts at 0 for a new game and only ever advances forward.

``last_real_time`` is the *only* wall-clock read left in the game: once
per tick we measure how much real time passed since the previous tick and
add that delta to ``elapsed_seconds``. Every other system works purely in
terms of this master timer, using a start/end-vs-master-timer pattern:
schedule an absolute ``*_at_seconds`` value, then compute "remaining" as
that value minus the current ``elapsed_seconds``.
"""

import datetime


def default_game_clock():
    """Return a fresh game_clock block for a new game (starts at 0)."""
    return {
        "elapsed_seconds": 0.0,
        "last_real_time": datetime.datetime.now().isoformat(),
    }


def get_game_clock(player_data):
    """Return the player_data game_clock block (always present on current saves)."""
    return player_data["game_clock"]


def advance(player_data):
    """Advance the master timer by the real time elapsed since the last call.

    Returns (elapsed_seconds, delta_seconds).
    """
    clock = get_game_clock(player_data)

    now = datetime.datetime.now()
    try:
        last_real_time = datetime.datetime.fromisoformat(clock["last_real_time"])
        delta_seconds = max(0.0, (now - last_real_time).total_seconds())
    except (TypeError, ValueError):
        delta_seconds = 0.0

    clock["elapsed_seconds"] = clock.get("elapsed_seconds", 0.0) + delta_seconds
    clock["last_real_time"] = now.isoformat()

    return clock["elapsed_seconds"], delta_seconds


def get_elapsed_seconds(player_data):
    """Return the current master timer value (seconds since new game)."""
    return get_game_clock(player_data).get("elapsed_seconds", 0.0)


def format_elapsed(seconds):
    """Format a duration as 'Hh Mm Ss', 'Mm Ss', or 'Ss' (largest units first)."""
    seconds = max(0, int(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)

    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    if minutes > 0:
        return f"{minutes}m {secs}s"
    return f"{secs}s"
