"""Shared power system constants and helpers."""


def default_station_power():
    """Return a fresh station_power dict for new games or missing save data.

    Discharge/charge no longer track their own wall-clock timestamp; the
    universal master game clock (see ``game_clock.py``) supplies the elapsed
    time used for these calculations.
    """
    return {
        "battery_level": 25.0,
        "solar_charging": False,
        "system_levels": {
            "life_support": 10,
            "hallway_lighting": 5,
            "security_systems": 7,
            "communication_array": 5,
        },
        "power_mode": "balanced",
        "last_lighting_battery_band": None,
    }


SYSTEM_POWER_RATES = {
    "life_support": 0.5,
    "hallway_lighting": 0.3,
    "security_systems": 0.3,
    "communication_array": 0.2,
}

LOW_POWER_SYSTEM_LEVELS = {
    "life_support": 7,
    "hallway_lighting": 3,
    "security_systems": 5,
    "communication_array": 2,
}

SOLAR_CHARGE_RATE = 3.0  # % per minute when solar array is active
HIGH_MODE_SOLAR_DRAIN = 0.5  # % per minute net loss when solar is on


def calculate_discharge(system_levels, elapsed_seconds, rates=SYSTEM_POWER_RATES):
    """Return total battery discharge (% of capacity) for the elapsed interval."""
    minutes = elapsed_seconds / 60
    total = 0.0
    for system, base_rate in rates.items():
        level = system_levels.get(system, 0)
        if level > 0:
            total += base_rate * level / 10.0 * minutes
    return total


def calculate_solar_charge(elapsed_seconds, solar_charging):
    """Return solar charge (% of capacity) for the elapsed interval."""
    if not solar_charging:
        return 0.0
    return (elapsed_seconds / 60) * SOLAR_CHARGE_RATE
