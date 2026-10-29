"""
Station layout modules live here, one file per map (e.g. donut.py).

Each map module exposes this interface:

    SHIP_MAP             -- dict of "x,y" -> {"name", "desc", ["locked"]}
    SPECIAL_ROOM_TILES    -- dict of "x,y" -> special room name (door tiles)
    SPECIAL_ROOM_HALLWAY  -- dict of "x,y" -> (x, y) hallway tile in front of it
    QUARTERS_LOCATION     -- dict {"x": int, "y": int} where a new game begins
    get_available_directions(x, y) -- dict of north/south/east/west bools
    render_map_text()     -- str, a readable text version of the map
"""
