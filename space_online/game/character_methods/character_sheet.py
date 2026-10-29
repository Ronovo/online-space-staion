import datetime

from space_online.game.helper_methods.health_bands import damage_band, health_band
from space_online.game.helper_methods.ui_panels import panel_action, register_panel
from space_online.game.objects.items import inventory_item_count

LIMB_ORDER = ["head", "chest", "left_arm", "right_arm", "left_leg", "right_leg"]
DAMAGE_TYPES = (("Burn", "burn"), ("Poison", "poison"), ("Oxygen", "oxygen"))


@register_panel("character_sheet", "Character Sheet")
def character_sheet_panel(game, state):
    player_data = game.player_data
    alcohol_value = player_data.setdefault("alcohol_percent", 0)

    damage_rows = []
    for label, key in DAMAGE_TYPES:
        value = player_data["damage"].get(key, 0)
        effect = None
        if value >= 30:
            effect = "Severe" if value >= 70 else "Moderate" if value >= 50 else "Mild"
        damage_rows.append({"name": label, "value": value, "color": damage_band(value)[1], "effect": effect})

    limbs = [
        {
            "name": limb.replace("_", " ").title(),
            "health": player_data["limbs"][limb],
            "color": health_band(player_data["limbs"][limb])[1],
        }
        for limb in LIMB_ORDER
        if limb in player_data["limbs"]
    ]

    limb_health = sum(player_data["limbs"].values()) / len(player_data["limbs"])
    damage_health = 100 - (sum(player_data["damage"].values()) / len(player_data["damage"]))

    return {
        "name": player_data["name"],
        "job": player_data["job"],
        "department": player_data.get("department", "Unknown"),
        "credits": player_data["credits"],
        "alcohol": alcohol_value,
        "alcohol_color": damage_band(alcohol_value)[1],
        "inventory_count": inventory_item_count(player_data),
        "holdings_count": len(player_data.get("stock_holdings", {})),
        "notes_count": len(player_data.get("notes", [])),
        "damage": damage_rows,
        "limbs": limbs,
        "damage_health": damage_health,
        "damage_health_color": health_band(damage_health)[1],
        "limb_health": limb_health,
        "limb_health_color": health_band(limb_health)[1],
    }


@panel_action("character_sheet", "inventory")
def open_inventory(game, state, args):
    game.open_panel("inventory")


@panel_action("character_sheet", "holdings")
def open_holdings(game, state, args):
    game.open_panel("holdings")


@panel_action("character_sheet", "notes")
def open_notes(game, state, args):
    game.open_panel("notes")


@register_panel("holdings", "Stock Holdings")
def holdings_panel(game, state):
    return {"holdings": list((game.player_data.get("stock_holdings") or {}).items())}


@register_panel("notes", "Character Notes")
def notes_panel(game, state):
    notes = []
    for note in reversed(game.player_data["notes"]):
        formatted_time = datetime.datetime.fromisoformat(note["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
        notes.append({"time": formatted_time, "text": note["text"]})
    return {"notes": notes}
