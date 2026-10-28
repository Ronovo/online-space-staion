# game/maps/donut.py
"""
The "Donut" station layout: a hollow square ring of hallways with special
rooms sprouting off of it (Bridge, MedBay, Security, Engineering, Bar,
Botany), plus the player's Quarters attached at the hallway junction.

This module is the single source of truth for this map's coordinates. Other
modules should import the constants/helpers below instead of hardcoding
"x,y" strings or coordinate math of their own.
"""

# --- Special room coordinate keys ---
# Defined once here so every file that needs a room's map key (door control,
# room UI modules, save/load code, etc.) imports the same value instead of
# retyping the literal string.
QUARTERS_KEY = "-1,0"
BRIDGE_KEY = "6,0"
MEDBAY_KEY = "0,6"
SECURITY_KEY = "6,6"
ENGINEERING_KEY = "6,3"
BAR_KEY = "-1,3"
BOTANY_KEY = "3,-1"

# Where a new game (or a player who somehow loses their location) starts.
QUARTERS_LOCATION = {"x": -1, "y": 0}

# --- Ship map: every tile's name/description/lock state ---
SHIP_MAP = {
    QUARTERS_KEY: {"name": "Quarters", "desc": "Your personal quarters on the station."},
    "0,0": {"name": "Hallway Junction", "desc": "A junction in the hallway. Your quarters are nearby."},
    "1,0": {"name": "North Hallway", "desc": "A long hallway stretching north."},
    "2,0": {"name": "North Hallway", "desc": "A long hallway stretching north."},
    "3,0": {"name": "North Hallway", "desc": "A long hallway stretching north. You notice a door labeled 'Botany Lab' on the west wall."},
    "4,0": {"name": "North Hallway", "desc": "A long hallway stretching north."},
    "5,0": {"name": "North End", "desc": "The northern end of the hallway. The bridge is nearby."},
    "0,1": {"name": "East Hallway", "desc": "A long hallway stretching east."},
    "0,2": {"name": "East Hallway", "desc": "A long hallway stretching east."},
    "0,3": {"name": "Bar Entrance", "desc": "This hallway leads to the station Bar. Soft music can be heard from inside."},
    "0,4": {"name": "East Hallway", "desc": "A long hallway stretching east."},
    "0,5": {"name": "East End", "desc": "The eastern end of the hallway. The medbay is nearby."},

    # Northeast Corridors
    "5,1": {"name": "Northeast Hallway", "desc": "A hallway connecting the north and east corridors."},
    "5,2": {"name": "Northeast Hallway", "desc": "A hallway connecting the north and east corridors."},
    "5,3": {"name": "Engineering Bay Entrance", "desc": "This hallway leads to the Engineering Bay."},
    "5,4": {"name": "Northeast Hallway", "desc": "A hallway connecting the north and east corridors."},
    "5,5": {"name": "Northeast Corner", "desc": "The far corner of the station. Security is nearby."},

    # East Section
    "4,5": {"name": "East Section", "desc": "A hallway along the eastern side of the station."},
    "3,5": {"name": "East Section", "desc": "A hallway along the eastern side of the station."},
    "2,5": {"name": "East Section", "desc": "A hallway along the eastern side of the station."},
    "1,5": {"name": "East Section", "desc": "A hallway connecting back to the main hallways."},

    # Special room tiles
    BRIDGE_KEY: {"name": "Bridge", "desc": "The control center of the station. The door is unlocked.", "locked": False},
    MEDBAY_KEY: {"name": "MedBay", "desc": "The medical facility of the station. The door is unlocked.", "locked": False},
    SECURITY_KEY: {"name": "Security", "desc": "The security center of the station. The door is unlocked.", "locked": False},
    ENGINEERING_KEY: {"name": "Engineering Bay", "desc": "The station's engineering and maintenance center. The door is unlocked.", "locked": False},
    BAR_KEY: {"name": "Bar", "desc": "The station's social hub where crew members can relax and enjoy drinks. The door is unlocked.", "locked": False},
    BOTANY_KEY: {"name": "Botany Lab", "desc": "The station's plant cultivation and research facility. The door is unlocked.", "locked": False},
}

# Which "x,y" tiles are special-room doors, and what the room is called.
SPECIAL_ROOM_TILES = {
    BRIDGE_KEY: "Bridge",
    MEDBAY_KEY: "MedBay",
    SECURITY_KEY: "Security",
    ENGINEERING_KEY: "Engineering",
    BAR_KEY: "Bar",
    BOTANY_KEY: "Botany",
    QUARTERS_KEY: "Quarters",
}

# Which hallway tile sits directly in front of each special room's door.
SPECIAL_ROOM_HALLWAY = {
    BRIDGE_KEY: (5, 0),
    MEDBAY_KEY: (0, 5),
    SECURITY_KEY: (5, 5),
    ENGINEERING_KEY: (5, 3),
    BAR_KEY: (0, 3),
    BOTANY_KEY: (3, 0),
    QUARTERS_KEY: (0, 0),
}

# Hallway tiles that replace the default N/S/E/W grid with a room button + corridor dirs.
# room_grid / dir grids are (row, column) for nav_frame.grid.
# check_available: only pack corridor dirs when get_available_directions allows them.
HALLWAY_SPECIAL_NAV = (
    {
        "hallway": SPECIAL_ROOM_HALLWAY[BRIDGE_KEY],
        "room_key": BRIDGE_KEY,
        "label": "Bridge",
        "room": "Bridge",
        "room_grid": (0, 1),
        "dirs": (("east", 1, 2), ("south", 2, 1)),
        "check_available": True,
    },
    {
        "hallway": SPECIAL_ROOM_HALLWAY[MEDBAY_KEY],
        "room_key": MEDBAY_KEY,
        "label": "MedBay",
        "room": "MedBay",
        "room_grid": (1, 2),
        "dirs": (("north", 0, 1), ("west", 1, 0)),
        "check_available": True,
    },
    {
        "hallway": SPECIAL_ROOM_HALLWAY[SECURITY_KEY],
        "room_key": SECURITY_KEY,
        "label": "Security",
        "room": "Security",
        "room_grid": (0, 1),
        "dirs": (("west", 1, 0), ("south", 2, 1)),
        "check_available": False,
    },
    {
        "hallway": SPECIAL_ROOM_HALLWAY[ENGINEERING_KEY],
        "room_key": ENGINEERING_KEY,
        "label": "Engineering Bay",
        "room": "Engineering",
        "room_grid": (0, 1),
        "dirs": (("west", 1, 0), ("east", 1, 2)),
        "check_available": False,
    },
    {
        "hallway": SPECIAL_ROOM_HALLWAY[BAR_KEY],
        "room_key": BAR_KEY,
        "label": "Bar",
        "room": "Bar",
        "room_grid": (2, 1),
        "dirs": (("west", 1, 0), ("east", 1, 2)),
        "check_available": False,
    },
)


def get_available_directions(x, y):
    """Return which of north/south/east/west lead to another tile on the ring.

    This encodes the shape of the donut: a hollow square hallway loop running
    along x == 0, x == 5, y == 0 and y == 5.
    """
    north = south = east = west = False

    # North hallway section (0-5, 0)
    if y == 0 and x < 5:
        north = True
    if y == 0 and x > 0:
        south = True

    # East hallway section (0, 0-5)
    if x == 0 and y < 5:
        east = True
    if x == 0 and y > 0:
        west = True

    # North end - can go east
    if x == 5 and y < 5:
        east = True
    if x == 5 and y > 0:
        west = True

    # East end - can go north
    if y == 5 and x < 5:
        north = True
    if y == 5 and x > 0:
        south = True

    return {"north": north, "south": south, "east": east, "west": west}


# --- Text map rendering ---
_CELL_WIDTH = 12


def _cell_display_name(key):
    """Return the label to print for a tile, or None if it's a plain hallway."""
    return SPECIAL_ROOM_TILES.get(key)


def render_map_text():
    """Build a readable text version of the map.

    Hallway tiles are drawn as a plain line; special rooms (and Quarters)
    are drawn with their name. Tiles that aren't part of the station are
    left blank, which is what leaves the hollow "donut hole" in the middle.
    """
    xs = []
    ys = []
    for key in SHIP_MAP:
        x_str, y_str = key.split(",")
        xs.append(int(x_str))
        ys.append(int(y_str))

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    lines = ["SPACE STATION EXPLORER - STATION MAP", ""]

    # North (higher x) at the top, east (higher y) to the right, to match the
    # "X North, Y East" location readout shown in the hallway view.
    for x in range(max_x, min_x - 1, -1):
        row_cells = []
        for y in range(min_y, max_y + 1):
            key = f"{x},{y}"
            if key not in SHIP_MAP:
                cell = ""
            else:
                room_name = _cell_display_name(key)
                cell = room_name if room_name else "-" * _CELL_WIDTH
            row_cells.append(cell.center(_CELL_WIDTH))
        lines.append("".join(row_cells).rstrip())

    lines.append("")
    lines.append("Lines are hallways. Named rooms are the station's special rooms.")

    return "\n".join(lines)
