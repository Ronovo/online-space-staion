"""Shared hallway/room lighting helpers."""

from space_online.game.helper_methods.power_constants import default_station_power

# Battery band -> allowed hallway_lighting range (inclusive)
LIGHTING_BANDS = {
    "normal": (6, 8),
    "dim": (3, 5),
    "emergency": (0, 2),
}


def battery_lighting_band(battery_level):
    """Return the lighting band suggested by battery percent."""
    if battery_level <= 5:
        return "emergency"
    if battery_level <= 15:
        return "dim"
    return "normal"


def clamp_lighting_for_battery(station_power):
    """Clamp hallway_lighting into the battery band when the band changes.

    Returns True if hallway_lighting was changed. Engineer overrides stick until
    the next battery-band transition.
    """
    if station_power is None:
        return False

    if "system_levels" not in station_power:
        station_power["system_levels"] = default_station_power()["system_levels"].copy()

    battery_level = station_power.get("battery_level", 100.0)
    band = battery_lighting_band(battery_level)
    last_band = station_power.get("last_lighting_battery_band")

    if last_band == band:
        return False

    low, high = LIGHTING_BANDS[band]
    levels = station_power["system_levels"]
    current = int(levels.get("hallway_lighting", 5))
    clamped = max(low, min(high, current))
    changed = clamped != current
    levels["hallway_lighting"] = clamped
    station_power["last_lighting_battery_band"] = band
    return changed


def lighting_style(hallway_lighting, place="hallway"):
    """Return bg/fg/power_desc for a hallway_lighting level.

    place should be \"hallway\" or \"room\" for the well-lit sentence.
    """
    level = int(hallway_lighting)
    place_word = "hallway" if place == "hallway" else "room"

    if level <= 2:
        return {
            "bg": "#220000",
            "fg": "#FF5555",
            "power_desc": "\n\nEmergency lighting casts an eerie red glow. Most systems are offline.",
        }
    if level <= 5:
        return {
            "bg": "#111111",
            "fg": "#BBBBBB",
            "power_desc": "\n\nThe lights are dimmed to conserve power.",
        }
    if level >= 9:
        return {
            "bg": "black",
            "fg": "white",
            "power_desc": f"\n\nThis {place_word} is very well lit.",
        }
    return {
        "bg": "black",
        "fg": "white",
        "power_desc": "",
    }


def ensure_station_power_lighting(player_data):
    """Ensure station_power exists and apply battery lighting clamp."""
    if "station_power" not in player_data:
        player_data["station_power"] = default_station_power()
    clamp_lighting_for_battery(player_data["station_power"])
    return player_data["station_power"]
