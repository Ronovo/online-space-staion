"""Player hallway movement: directional travel and alcohol impairment checks."""

import random

from space_online.game.helper_methods.alcohol_helper import stumble_chance, fall_chance
from space_online.game.helper_methods.game_clock import get_elapsed_seconds
from space_online.game.helper_methods.jail import (
    format_jail_time,
    is_jailed,
    jail_seconds_remaining,
)
from space_online.game.helper_methods.npc_movement import find_hall_passersby
from space_online.game.helper_methods.random_events import maybe_trigger_hallway_event

DIRECTION_STEPS = {
    "north": (1, 0),
    "south": (-1, 0),
    "east": (0, 1),
    "west": (0, -1),
}


class PlayerMovementMixin:
    def _try_alcohol_movement_impairment(self):
        """Roll stumble (then optional fall) before moving. Return True if move is cancelled."""
        alcohol = self.player_data.get("alcohol_percent", 0) or 0
        s_chance = stumble_chance(alcohol)
        if s_chance <= 0 or random.random() >= (s_chance / 100.0):
            return False

        f_chance = fall_chance(alcohol)
        if f_chance > 0 and random.random() < (f_chance / 100.0):
            limbs = self.player_data.get("limbs") or {}
            if limbs:
                limb = random.choice(list(limbs.keys()))
                damage = random.randint(1, 5)
                original_health = limbs[limb]
                limbs[limb] = max(0, original_health - damage)
                limb_name = limb.replace("_", " ").title()
                self.alert(
                    "You Fall",
                    f"You stumble and fall hard!\n\n"
                    f"Your {limb_name} took {damage}% blunt damage "
                    f"and is now at {limbs[limb]}%.",
                )
                self.add_note(
                    f"Fell while intoxicated ({alcohol:.1f}% alcohol). "
                    f"{limb_name} took {damage}% blunt damage "
                    f"(from {original_health}% to {limbs[limb]}%)."
                )
            else:
                self.alert("You Fall", "You stumble and fall hard!")
                self.add_note(f"Fell while intoxicated ({alcohol:.1f}% alcohol).")
            return True

        self.alert(
            "You Stumble",
            "You stumble and lose your footing. You stay where you are.",
        )
        self.add_note(
            f"Stumbled while intoxicated ({alcohol:.1f}% alcohol) and failed to move."
        )
        return True

    def move_direction(self, direction):
        if direction not in DIRECTION_STEPS:
            return

        if is_jailed(self.player_data):
            remaining = format_jail_time(
                jail_seconds_remaining(self.player_data, get_elapsed_seconds(self.player_data))
            )
            self.alert("In Jail", f"You are in jail. Time remaining: {remaining}.")
            return

        if self._try_alcohol_movement_impairment():
            return

        dx, dy = DIRECTION_STEPS[direction]
        x = self.player_data["location"]["x"] + dx
        y = self.player_data["location"]["y"] + dy

        if f"{x},{y}" not in self.ship_map:
            self.alert("Error", "You can't go that way!", kind="error")
            return

        self.player_data["location"] = {"x": x, "y": y}

        maybe_trigger_hallway_event(self)

        if is_jailed(self.player_data):
            return

        # Hallway passers-by are checked on every move.
        for npc in find_hall_passersby(self.player_data, self.station_crew):
            if self._handle_hallway_security_encounter(npc):
                if is_jailed(self.player_data):
                    return
                continue
            self.alert(
                "Crew Encounter",
                f"{npc.get('name', 'A crew member')} ({npc.get('job', 'Crew')}) passes you in the hall.",
            )
