"""Alcohol intoxication helpers: decay, stumble/fall chances, sober-up cost."""

ALCOHOL_DECAY_SECONDS = 120
ALCOHOL_DECAY_AMOUNT = 5
DOCTOR_SOBER_FLOOR = 25


def apply_alcohol_tick(player_data, elapsed_seconds):
    """Decay alcohol_percent by 5% per ALCOHOL_DECAY_SECONDS while above 0.

    Uses an accumulator in player_data["damage_timers"]["alcohol_decay_acc"]
    so partial intervals carry across battery ticks.
    """
    alcohol = player_data.get("alcohol_percent", 0) or 0
    if alcohol <= 0 or elapsed_seconds <= 0:
        return

    timers = player_data.setdefault("damage_timers", {})
    acc = timers.get("alcohol_decay_acc", 0.0) + float(elapsed_seconds)
    decayed = 0
    while acc >= ALCOHOL_DECAY_SECONDS and alcohol > 0:
        acc -= ALCOHOL_DECAY_SECONDS
        alcohol = max(0, alcohol - ALCOHOL_DECAY_AMOUNT)
        decayed += ALCOHOL_DECAY_AMOUNT

    timers["alcohol_decay_acc"] = acc
    if decayed:
        player_data["alcohol_percent"] = alcohol
        if alcohol <= 0:
            timers["alcohol_decay_acc"] = 0.0


def stumble_chance(alcohol):
    """Return stumble chance as an integer percent (0-100) for the given BAC."""
    if alcohol is None or alcohol <= 5:
        return 0
    if alcohol < 10:
        return 10
    if alcohol < 15:
        return 15
    if alcohol < 20:
        return 20
    if alcohol < 25:
        return 25
    if alcohol < 50:
        return 35
    if alcohol < 75:
        return 55
    if alcohol < 100:
        return 75
    return 80


def fall_chance(alcohol):
    """Return fall chance as an integer percent (0-100), only after a stumble.

    Fall is only possible at alcohol >= 25%.
    """
    if alcohol is None or alcohol < 25:
        return 0
    if alcohol < 50:
        return 25
    if alcohol < 75:
        return 35
    if alcohol < 100:
        return 50
    return 75


def sober_up_cost(alcohol):
    """Credits to sober up: int(alcohol) when at/above DOCTOR_SOBER_FLOOR, else 0."""
    if alcohol is None or alcohol < DOCTOR_SOBER_FLOOR:
        return 0
    return int(alcohol)
