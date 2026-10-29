import json

import pytest

from space_online.game.character_methods.character_creation import (
    JOBS,
    MAX_NAME_LENGTH,
    SELECT_DEPARTMENT,
    create_character,
    group_jobs_by_department,
)
from space_online.game.helper_methods.door_control import SPECIAL_ROOM_DOORS, can_control_door
from space_online.game.helper_methods.oxygen_helper import oxygen_damage_for_tick
from space_online.game.main import SpaceStationGame
from space_online.game.helper_methods.random_events import build_job_event
from space_online.game.helper_methods.stock_market import round_credits
from space_online.game.maps.donut import BRIDGE_KEY, MEDBAY_KEY, QUARTERS_LOCATION
from space_online.game.objects import botany_items
from space_online.game.objects.botany_items import BOTANY_SEED_IDS, refresh_planter_growth
from space_online.game.objects.drinks import MAX_GLASS_POURS, add_ingredient
from space_online.game.objects.items import add_to_inventory, get_item_definition, inventory_item_count
from space_online.game.special_rooms.engineering import _update_system_level
from space_online.game.special_rooms.security import pardon
from space_online.game.special_rooms.shared import MAX_NOTES, add_note


def test_every_job_is_listed_under_exactly_one_department():
    listed = [job for _, jobs in group_jobs_by_department() for job in jobs]
    assert sorted(listed) == sorted(JOBS)


def test_create_character_uses_job_details():
    player = create_character("  Ada  ", "Medical", "Doctor")
    assert player["name"] == "Ada"
    assert player["credits"] == JOBS["Doctor"]["credits"]
    assert player["subdepartment"] == "Doctor"
    assert can_control_door(player, MEDBAY_KEY)
    assert not can_control_door(player, BRIDGE_KEY)


def test_captain_can_work_every_door():
    captain = create_character("Cap", "Administration", "Captain")
    assert all(can_control_door(captain, door) for door in SPECIAL_ROOM_DOORS)


@pytest.mark.parametrize("name, department, job, message", [
    ("", "Civilian", "Staff Assistant", "Please enter a character name."),
    ("x" * (MAX_NAME_LENGTH + 1), "Civilian", "Staff Assistant", "at most"),
    ("Ada", SELECT_DEPARTMENT, "Staff Assistant", "Please select a department."),
    ("Ada", "Civilian", "Engineer", "Please select a job."),
    ("Ada", "Civilian", "Not A Job", "Please select a job."),
])
def test_create_character_rejects_bad_input(name, department, job, message):
    with pytest.raises(ValueError, match=message):
        create_character(name, department, job)


def test_door_control_follows_job():
    captain = create_character("Cap", "Administration", "Captain")
    doctor = create_character("Doc", "Medical", "Doctor")
    assistant = create_character("Sam", "Civilian", "Staff Assistant")

    assert all(can_control_door(captain, key) for key in SPECIAL_ROOM_DOORS)
    assert [key for key in SPECIAL_ROOM_DOORS if can_control_door(doctor, key)] == [MEDBAY_KEY]
    assert not any(can_control_door(assistant, key) for key in SPECIAL_ROOM_DOORS)
    assert not can_control_door(captain, "no-such-door")


def test_inventory_stacks_items_except_basic_tools():
    player = {"inventory": []}
    wrench = get_item_definition("wrench")
    add_to_inventory(player, wrench)
    add_to_inventory(player, wrench)
    assert len(player["inventory"]) == 1
    assert inventory_item_count(player) == 2

    tools = get_item_definition("basic_tools")
    add_to_inventory(player, tools)
    add_to_inventory(player, tools)
    assert len(player["inventory"]) == 3
    assert inventory_item_count(player) == 4


def test_game_ticks_renders_and_saves_as_json():
    game = SpaceStationGame(create_character("Ada", "Civilian", "Staff Assistant"))
    game.player_data["game_clock"]["last_real_time"] -= 5
    game.tick()
    assert game.player_data["game_clock"]["elapsed_seconds"] >= 5
    view = game.view()
    assert view["title"]
    assert view["redirect"] is None
    json.dumps(game.to_save_data())


def test_oxygen_damage_adds_up_over_short_ticks():
    player = create_character("Ada", "Civilian", "Staff Assistant")
    for _ in range(120):
        oxygen_damage = oxygen_damage_for_tick(player, 0, 1.0)
        player["damage"]["oxygen"] += oxygen_damage
    assert player["damage"]["oxygen"] > 0


def test_restoring_life_support_clears_the_emergency_announcement():
    game = SpaceStationGame(create_character("Ada", "Engineering", "Engineer"))
    _update_system_level(game, "life_support", 0)
    assert game.player_data["announcements"]
    _update_system_level(game, "life_support", 10)
    assert "announcements" not in game.player_data


def test_notes_keep_only_the_newest():
    player = create_character("Ada", "Civilian", "Staff Assistant")
    for n in range(MAX_NOTES + 5):
        add_note(player, f"note {n}")
    assert len(player["notes"]) == MAX_NOTES
    assert player["notes"][-1]["text"] == f"note {MAX_NOTES + 4}"


@pytest.mark.parametrize("due, stage, dead", [(2, 2, False), (4, 2, True)])
def test_one_watering_carries_a_plant_through_one_stage(monkeypatch, due, stage, dead):
    monkeypatch.setattr(botany_items, "compute_growth_stage", lambda *args: due)
    planter = {"occupied": True, "planted_at_seconds": 0, "growth_stage": 1, "watered": True, "growth_class": "fast"}
    assert refresh_planter_growth(planter, 999) == stage
    assert planter.get("dead", False) is dead
    assert planter["watered"] is False


def test_a_jailed_player_cannot_pardon_anyone():
    game = SpaceStationGame(create_character("Ada", "Security", "Security Guard"))
    game.player_data["in_jail"] = True
    pardon(game, {"selected": -1}, {})
    assert game.player_data["in_jail"] is True


def test_an_invalid_location_goes_back_to_quarters():
    game = SpaceStationGame(create_character("Ada", "Civilian", "Staff Assistant"))
    game.player_data["location"] = {"x": 999, "y": 999}
    game._normalize_location()
    assert game.player_data["location"] == QUARTERS_LOCATION


def test_the_mixer_glass_has_a_limit():
    game = SpaceStationGame(create_character("Ada", "Civilian", "Bartender"))
    state = {"selected_ingredient": "Vodka", "glass": ["Vodka"] * MAX_GLASS_POURS}
    add_ingredient(game, state, {})
    assert len(state["glass"]) == MAX_GLASS_POURS


def test_the_botanist_is_only_asked_for_crops_botany_grows():
    game = SpaceStationGame(create_character("Ada", "Civilian", "Botanist"))
    crops = {seed.removesuffix("_seeds") for seed in BOTANY_SEED_IDS}
    for _ in range(20):
        event = build_job_event(game)
        assert any(f" {crop} " in event["desc"] for crop in crops)


def test_credits_round_to_the_cent():
    assert round_credits(0.29) == 0.29
    assert round_credits(10.005 + 0.001) == 10.01
