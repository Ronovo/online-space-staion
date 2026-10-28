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
from space_online.game.main import SpaceStationGame
from space_online.game.maps.donut import MEDBAY_KEY
from space_online.game.objects.items import add_to_inventory, get_item_definition, inventory_item_count


def test_every_job_is_listed_under_exactly_one_department():
    listed = [job for _, jobs in group_jobs_by_department() for job in jobs]
    assert sorted(listed) == sorted(JOBS)


def test_create_character_uses_job_details():
    player = create_character("  Ada  ", "Medical", "Doctor")
    assert player["name"] == "Ada"
    assert player["credits"] == JOBS["Doctor"]["credits"]
    assert player["subdepartment"] == "Doctor"
    assert player["permissions"]["medbay_station"] is True
    assert player["permissions"]["bridge_station"] is False


def test_captain_has_every_permission():
    assert all(create_character("Cap", "Administration", "Captain")["permissions"].values())


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
    game.tick()
    view = game.view()
    assert view["title"]
    assert view["redirect"] is None
    json.dumps(game.to_save_data())
