from space_online.game.maps.donut import (
    BRIDGE_KEY,
    MEDBAY_KEY,
    SECURITY_KEY,
    ENGINEERING_KEY,
    BAR_KEY,
    BOTANY_KEY,
)

SPECIAL_ROOM_DOORS = {
    BRIDGE_KEY: {
        "room_name": "Bridge",
        "desc_base": "The control center of the station.",
        "permission": frozenset({"Captain", "HoP"}),
    },
    MEDBAY_KEY: {
        "room_name": "MedBay",
        "desc_base": "The medical facility of the station.",
        "permission": frozenset({"Captain", "HoP", "Doctor"}),
    },
    SECURITY_KEY: {
        "room_name": "Security",
        "desc_base": "The security center of the station.",
        "permission": frozenset({"Captain", "Security"}),
    },
    ENGINEERING_KEY: {
        "room_name": "Engineering Bay",
        "desc_base": "The station's engineering and maintenance center.",
        "permission": frozenset({"Captain", "HoP", "Engineer"}),
    },
    BAR_KEY: {
        "room_name": "Bar",
        "desc_base": "The station's social hub where crew members can relax and enjoy drinks.",
        "permission": frozenset({"Captain", "HoP", "Bar"}),
    },
    BOTANY_KEY: {
        "room_name": "Botany Lab",
        "desc_base": "The station's plant cultivation and research facility.",
        "permission": frozenset({"Captain", "HoP", "Botany"}),
    },
}

ACCESS_ERROR = "Unable to access door control system."


def can_control_door(player_data, door_key):
    door = SPECIAL_ROOM_DOORS.get(door_key)
    if not door:
        return False
    return player_data.get("subdepartment", "") in door.get("permission", frozenset())


def is_door_locked(player_data, door_key):
    return player_data.get("ship_map", {}).get(door_key, {}).get("locked", False)


def toggle_door_lock(game, door_key):
    player_data = game.player_data
    ship_map = player_data.get("ship_map", {})
    if not can_control_door(player_data, door_key) or door_key not in ship_map:
        game.alert("Door Control", ACCESS_ERROR)
        return False

    door = SPECIAL_ROOM_DOORS[door_key]
    room_name = door["room_name"]
    desc_base = door["desc_base"]

    if ship_map[door_key].get("locked", False):
        ship_map[door_key]["locked"] = False
        ship_map[door_key]["desc"] = f"{desc_base} The door is unlocked."
        message = f"The {room_name} door has been unlocked."
    else:
        ship_map[door_key]["locked"] = True
        ship_map[door_key]["desc"] = f"{desc_base} The door is locked."
        message = f"The {room_name} door has been locked."

    game.alert("Door Control", message)
    return True
