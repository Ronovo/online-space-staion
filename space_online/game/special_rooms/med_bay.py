import math

from space_online.game.helper_methods.oxygen_helper import DOCTOR_REQUIRED_FLOOR
from space_online.game.helper_methods.alcohol_helper import DOCTOR_SOBER_FLOOR, sober_up_cost
from space_online.game.helper_methods.station_status import crew_health_status
from space_online.game.special_rooms.shared import (
    SpecialRoomBase,
    available_npc,
    button,
    npc_contact_widgets,
    room_action,
)
from space_online.game.helper_methods.ui_panels import choice_handler, panel_action, register_panel
from space_online.game.maps.donut import MEDBAY_KEY

# Cost multipliers: 1 credit per damage point, with type-based scaling
COST_MULTIPLIERS = {
    "blunt": 1,
    "poison": 2,
    "oxygen": 2,
    "burn": 3,
}

NON_LIMB_DAMAGE_TYPES = ("burn", "poison", "oxygen")


def _limb_status(health):
    if health > 75:
        return "Healthy"
    if health > 40:
        return "Injured"
    return "Critical"


def _non_limb_status(damage_val):
    if damage_val < 10:
        return "Clear"
    if damage_val < 30:
        return "Mild"
    if damage_val < 60:
        return "Moderate"
    return "Severe"


def assess_injuries(player_data):
    """Return limb/non-limb damage breakdown and treatment costs."""
    limbs = player_data.get("limbs", {}) or {}
    damage = player_data.get("damage", {}) or {}

    limb_details = []
    blunt_points = 0
    injured_limbs = []
    critical_limbs = []

    for limb, health in limbs.items():
        limb_name = limb.replace("_", " ").title()
        points = max(0, 100 - health)
        blunt_points += points
        status = _limb_status(health)
        limb_details.append({
            "key": limb,
            "name": limb_name,
            "health": health,
            "points": points,
            "status": status,
        })
        if status == "Injured":
            injured_limbs.append(limb_name)
        elif status == "Critical":
            critical_limbs.append(limb_name)

    non_limb = {}
    for dtype in NON_LIMB_DAMAGE_TYPES:
        value = damage.get(dtype, 0) or 0
        non_limb[dtype] = {
            "value": value,
            "status": _non_limb_status(value),
            "multiplier": COST_MULTIPLIERS[dtype],
            "cost": math.ceil(value * COST_MULTIPLIERS[dtype]) if value > 0 else 0,
        }

    blunt_cost = math.ceil(blunt_points * COST_MULTIPLIERS["blunt"]) if blunt_points > 0 else 0
    burn_cost = non_limb["burn"]["cost"]
    poison_cost = non_limb["poison"]["cost"]
    oxygen_cost = non_limb["oxygen"]["cost"]
    total_cost = blunt_cost + burn_cost + poison_cost + oxygen_cost

    overall_limb_health = 0.0
    if limbs:
        overall_limb_health = (sum(limbs.values()) / (len(limbs) * 100)) * 100

    active_damage_types = [
        dtype.title() for dtype in NON_LIMB_DAMAGE_TYPES if non_limb[dtype]["value"] > 0
    ]

    return {
        "limbs": limbs,
        "limb_details": limb_details,
        "injured_limbs": injured_limbs,
        "critical_limbs": critical_limbs,
        "overall_limb_health": overall_limb_health,
        "blunt_points": blunt_points,
        "blunt_cost": blunt_cost,
        "non_limb": non_limb,
        "active_damage_types": active_damage_types,
        "burn_cost": burn_cost,
        "poison_cost": poison_cost,
        "oxygen_cost": oxygen_cost,
        "total_cost": total_cost,
    }


def format_cost_breakdown(assessment):
    """Itemized treatment cost lines for popups."""
    lines = []
    if assessment["blunt_points"] > 0:
        lines.append(
            f"- Blunt: {assessment['blunt_points']:.0f} pts × {COST_MULTIPLIERS['blunt']} "
            f"= {assessment['blunt_cost']} credits"
        )
    for dtype in NON_LIMB_DAMAGE_TYPES:
        info = assessment["non_limb"][dtype]
        if info["value"] > 0:
            lines.append(
                f"- {dtype.title()}: {info['value']:.0f} pts × {info['multiplier']} "
                f"= {info['cost']} credits"
            )
    return lines


def format_damage_sections(assessment):
    """Limb and other-damage sections shared by health check and doctor dialogs."""
    sections = []

    if assessment["limb_details"]:
        limb_lines = ["Limb Status:"]
        for limb in assessment["limb_details"]:
            limb_lines.append(
                f"- {limb['name']}: {limb['health']}% ({limb['status']})"
            )
        sections.append("\n".join(limb_lines))
    else:
        sections.append("Limb Status:\nNo limb health data available.")

    damage_lines = ["Other Damage:"]
    for dtype in NON_LIMB_DAMAGE_TYPES:
        info = assessment["non_limb"][dtype]
        damage_lines.append(
            f"- {dtype.title()}: {info['value']:.1f}% ({info['status']})"
        )
    sections.append("\n".join(damage_lines))

    return "\n\n".join(sections)


def build_treatment_cost_block(assessment, alcohol=0):
    """Shared cost totals and breakdown lines for health check / doctor dialogs."""
    sober_cost = sober_up_cost(alcohol)
    injury_cost = assessment["total_cost"]
    total_cost = injury_cost + sober_cost
    lines = ["Treatment Cost:"]
    lines.extend(format_cost_breakdown(assessment))
    if sober_cost > 0:
        lines.append(f"- Sober up: {sober_cost} credits")
    lines.append(f"Total: {total_cost} credits")
    return {
        "injury_cost": injury_cost,
        "sober_cost": sober_cost,
        "total_cost": total_cost,
        "lines": lines,
    }


def build_health_check_report(player_data):
    """Full health-check report text (scan results + recommendation + costs)."""
    assessment = assess_injuries(player_data)
    overall_health = assessment["overall_limb_health"]
    has_non_limb = bool(assessment["active_damage_types"])
    alcohol = player_data.get("alcohol_percent", 0) or 0
    sober_cost = sober_up_cost(alcohol)

    health_report = "Health Check Results:\n\n"
    if assessment["limbs"]:
        health_report += f"Overall Limb Health: {overall_health:.1f}%\n\n"
    health_report += format_damage_sections(assessment)

    if alcohol > 0:
        health_report += f"\n\nBlood Alcohol: {alcohol:.1f}%"
        if alcohol >= DOCTOR_SOBER_FLOOR:
            health_report += (
                f"\n• Intoxication is at or above {DOCTOR_SOBER_FLOOR}%. "
                f"Doctor treatment is required to sober up "
                f"({sober_cost} credits)."
            )
        else:
            health_report += (
                "\n• Alcohol will metabolize over time "
                "(about 5% every 2 minutes)."
            )

    needs_attention = overall_health < 60 or has_non_limb or alcohol >= DOCTOR_SOBER_FLOOR
    health_report += "\n\nRecommendation: "
    if needs_attention:
        health_report += "Medical attention recommended."
    else:
        health_report += "No immediate medical attention required."

    if overall_health < 100 or has_non_limb:
        health_report += "\n\nDetailed Notes:"

        if assessment["critical_limbs"]:
            health_report += f"\n• Critical damage detected in {', '.join(assessment['critical_limbs'])}. "
            health_report += "Immediate treatment required."

        if assessment["injured_limbs"]:
            health_report += f"\n• Moderate trauma detected in {', '.join(assessment['injured_limbs'])}. "
            health_report += "Rest and treatment advised."

        if has_non_limb:
            health_report += (
                f"\n• Non-limb damage detected: {', '.join(assessment['active_damage_types'])}."
            )

        oxygen_damage = assessment["non_limb"]["oxygen"]["value"]
        if oxygen_damage > 0:
            if oxygen_damage >= DOCTOR_REQUIRED_FLOOR:
                health_report += (
                    f"\n• Oxygen damage is at {oxygen_damage:.0f}% "
                    f"(at or above {DOCTOR_REQUIRED_FLOOR}%). "
                    "You must be healed by the doctor to fully recover."
                )
            else:
                health_report += (
                    f"\n• Oxygen damage is at {oxygen_damage:.0f}% "
                    f"(below {DOCTOR_REQUIRED_FLOOR}%). "
                    "You can rest to restore yourself while life support is functional."
                )

        if overall_health < 75:
            health_report += "\n• Movement and performance significantly impaired."
        elif overall_health < 90 and assessment["limbs"]:
            health_report += "\n• Some physical activities may be difficult."

    cost = build_treatment_cost_block(assessment, alcohol)
    if cost["total_cost"] > 0:
        health_report += "\n\nEstimated Treatment Cost:"
        for line in format_cost_breakdown(assessment):
            health_report += f"\n{line}"
        if cost["sober_cost"] > 0:
            health_report += f"\n- Sober up: {cost['sober_cost']} credits"
        health_report += f"\nTotal: {cost['total_cost']} credits"
        health_report += "\n(Talk to Doctor to receive treatment)"
    else:
        health_report += "\n\nNo treatment needed."

    return health_report


def build_doctor_exam_message(player_data):
    """Doctor dialog body + cost totals for treatment confirmation."""
    assessment = assess_injuries(player_data)
    alcohol = player_data.get("alcohol_percent", 0) or 0
    cost = build_treatment_cost_block(assessment, alcohol)

    if cost["total_cost"] == 0:
        return {
            "assessment": assessment,
            "alcohol": alcohol,
            **cost,
            "message": "The doctor examines you. 'You're in perfect health! No treatment needed.'",
            "needs_treatment": False,
        }

    message = "The doctor examines you.\n\n"
    message += format_damage_sections(assessment)
    if alcohol > 0:
        message += f"\n\nBlood Alcohol: {alcohol:.1f}%"
    message += "\n\n" + "\n".join(cost["lines"])
    message += "\n\nWould you like to proceed with treatment?"
    return {
        "assessment": assessment,
        "alcohol": alcohol,
        **cost,
        "message": message,
        "needs_treatment": True,
    }


class MedBay(SpecialRoomBase):
    ROOM_TITLE = "MedBay"
    ROOM_HEADING = "Station Medical Bay"
    ROOM_DESCRIPTION = (
        "The medical bay is clean and orderly. Various medical equipment lines the walls, and a few "
        "examination beds are visible. The station's medical staff handle everything from routine "
        "checkups to emergency trauma care."
    )
    DOOR_KEY = MEDBAY_KEY
    STATION_ENTRIES = ({"label": "Enter MedBay Station", "mode": "medbay_station"},)
    CONTACT_JOBS = ("Doctor",)

    def room_options(self):
        widgets = [button("Request Health Check", "room.health_check")]
        widgets += npc_contact_widgets(
            self.game,
            "Doctor",
            talk_label="Talk to Doctor",
            talk_action="talk_to_doctor",
            absent_flavor="The doctor is currently away from MedBay.",
        )
        return widgets + self.back_to_station_menu()

    def mode_buttons(self, mode):
        if mode != "medbay_station" or not self.station_allowed(mode):
            return None
        return [
            button("Heal Injuries", "room.heal_player"),
            button("Check Crew Vitals", "room.show_crew_vitals"),
            button("Back to Station Menu", "room.set_mode", mode="menu"),
        ]

    @room_action
    def health_check(self):
        self.game.alert("Medical Scan", build_health_check_report(self.player_data))

    @room_action
    def talk_to_doctor(self):
        """Talk to a doctor who can provide healing for a fee based on damage"""
        if available_npc(self.game, "Doctor") is None:
            return
        exam = build_doctor_exam_message(self.player_data)
        if not exam["needs_treatment"]:
            self.game.alert("Doctor", exam["message"])
            return

        self.game.ask(
            "Doctor",
            exam["message"],
            [
                (
                    f"Yes ({exam['total_cost']} credits)",
                    "doctor_treatment",
                    {"total_cost": exam["total_cost"], "sober_cost": exam["sober_cost"]},
                ),
                ("No", None, None),
            ],
        )

    @room_action(station="medbay_station")
    def heal_player(self):
        """Heal the player's limbs to full health"""
        original_health = self.player_data["limbs"].copy()
        for limb in self.player_data["limbs"]:
            self.player_data["limbs"][limb] = 100

        healing_report = "Medical Treatment Results:\n\n"
        healing_report += "All limbs restored to full health.\n\n"
        healing_report += "Previous Status:\n"

        injury_details = []
        for limb, health in original_health.items():
            limb_name = limb.replace("_", " ").title()
            healing_report += f"- {limb_name}: {health}% → 100%\n"
            if health < 100:
                injury_details.append(f"{limb_name} ({health}% → 100%)")

        self.game.alert("Medical Treatment", healing_report)
        if injury_details:
            self.add_note(
                f"Received advanced medical treatment at MedBay Station. Healed: {', '.join(injury_details)}"
            )

    @room_action(station="medbay_station")
    def show_crew_vitals(self):
        self.game.open_panel("crew_vitals")


@choice_handler("doctor_treatment")
def pay_for_healing(game, total_cost, sober_cost=0):
    """Pay credits for healing based on the calculated cost"""
    player_data = game.player_data
    if player_data["credits"] < total_cost:
        game.alert(
            "Doctor",
            "You don't have enough credits for treatment. Come back when you can afford it.",
        )
        return

    player_data["credits"] -= total_cost

    original_health = player_data["limbs"].copy()
    original_damage = player_data["damage"].copy()
    original_alcohol = player_data.get("alcohol_percent", 0) or 0

    for limb in player_data["limbs"]:
        player_data["limbs"][limb] = 100
    for damage_type in player_data["damage"]:
        player_data["damage"][damage_type] = 0

    sobered = False
    if sober_cost > 0:
        player_data["alcohol_percent"] = 0
        player_data.setdefault("damage_timers", {})["alcohol_decay_acc"] = 0.0
        sobered = True

    injured_limbs = [
        limb.replace("_", " ").title() for limb, health in original_health.items() if health < 100
    ]
    injured_damage = [dtype.title() for dtype, value in original_damage.items() if value > 0]
    has_injuries = bool(injured_limbs) or bool(injured_damage)

    message = f"You pay {total_cost} credits. The doctor treats you.\n\n"
    if has_injuries:
        message += "Healed:\n"
        if injured_limbs:
            message += f"- Blunt damage: {', '.join(injured_limbs)}\n"
        if injured_damage:
            message += f"- Other damage: {', '.join(injured_damage)}\n"
    if sobered:
        message += f"- Intoxication cleared (was {original_alcohol:.1f}%).\n"
    if has_injuries or sobered:
        message += "\nYou feel much better now."
    else:
        message += "No injuries were found."
    game.alert("Treatment Complete", message)

    if has_injuries or sobered:
        healed_parts = []
        if injured_limbs:
            healed_parts.append(f"Blunt Damage ({', '.join(injured_limbs)}) fully healed.")
        if injured_damage:
            healed_parts.append(f"Other Damage ({', '.join(injured_damage)}) fully healed.")
        if sobered:
            healed_parts.append(f"Sobered up from {original_alcohol:.1f}% alcohol.")
        note_text = f"Paid {total_cost} credits for medical treatment. {'. '.join(healed_parts)}"
    else:
        note_text = f"Paid {total_cost} credits for medical examination. No injuries were found."
    game.add_note(note_text)


VITALS_STATUS_COLORS = {"Healthy": "green", "Injured": "yellow", "Critical": "red"}
VITALS_DAMAGE_ICONS = {"burn": "🔥", "poison": "☣️", "oxygen": "💨"}


def _vitals_color(value, *, damage=False):
    if damage:
        return "green" if value < 10 else "yellow" if value < 30 else "orange" if value < 60 else "red"
    return "green" if value > 75 else "yellow" if value > 40 else "red"


@register_panel("crew_vitals", "Crew Vitals Monitor")
def crew_vitals_panel(game, state):
    crew = []
    for crew_member in [game.player_data] + game.station_crew:
        status = crew_health_status(crew_member)
        limbs = crew_member.get("limbs", {})
        damage = crew_member.get("damage", {})
        crew.append({
            "name": crew_member.get("name", "N/A"),
            "job": crew_member.get("job", "N/A"),
            "is_player": crew_member is game.player_data,
            "status": status,
            "status_color": VITALS_STATUS_COLORS[status],
            "limbs": [
                {"name": limb.replace("_", " ").title(), "health": health, "color": _vitals_color(health)}
                for limb, health in limbs.items()
            ],
            "damage": [
                {
                    "icon": icon,
                    "name": dtype.title(),
                    "value": damage.get(dtype, 0),
                    "color": _vitals_color(damage.get(dtype, 0), damage=True),
                }
                for dtype, icon in VITALS_DAMAGE_ICONS.items()
            ],
        })
    return {"crew": crew, "details": bool(state.get("details"))}


@panel_action("crew_vitals")
def toggle_details(game, state, args):
    state["details"] = not state.get("details")
