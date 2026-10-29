"""Shared oxygen / life-support damage helpers."""

from space_online.game.maps import donut

# Tick / damage scale
OXYGEN_TICK_SECONDS = 15
BASE_DAMAGE_PER_TICK = 4
DAMAGE_THRESHOLD_LEVEL = 4  # life support <= this applies damage
DOCTOR_REQUIRED_FLOOR = 25
WARNING_THRESHOLDS = (30, 60, 90)
DEATH_THRESHOLD = 100
POST_DEATH_OXYGEN = 50
POST_DEATH_LIMB_HEALTH = 20
RECOVERY_SECONDS_PER_PERCENT = 30

# Grace period (master-timer seconds) between life support hitting 0 and
# oxygen damage actually starting, per the station-wide emergency announcement.
OXYGEN_DEPLETION_GRACE_SECONDS = 15

# Player warning messages (keyed by threshold %)
OXYGEN_WARNING_MESSAGES = {
    30: "You're feeling light-headed and having difficulty breathing. Oxygen levels are dropping.",
    60: "Your vision is beginning to blur and you're experiencing severe difficulty breathing. Oxygen deprivation is worsening.",
    90: "You're on the verge of losing consciousness. Severe oxygen deprivation detected. Immediate action required.",
}

OXYGEN_DEATH_TITLE = "CRITICAL: Oxygen Depleted"
OXYGEN_DEATH_MESSAGE = (
    "You have succumbed to oxygen deprivation. Emergency medical protocols have been "
    "activated, and you have been revived at minimal health levels."
)
OXYGEN_DEATH_NOTE = (
    "CRITICAL EVENT: Nearly died from oxygen deprivation. Emergency medical systems intervened."
)

# Engineering panel alerts
LIFE_SUPPORT_DAMAGE_BEGIN_TITLE = "Life Support Warning"
LIFE_SUPPORT_DAMAGE_BEGIN_MESSAGE = "Oxygen damage to crew will begin"

OXYGEN_DEPLETION_ANNOUNCEMENT_TEXT = (
    "CRITICAL ALERT: Life support systems offline! Oxygen levels dropping to critical levels. "
    "All crew are advised to evacuate or obtain emergency oxygen supplies immediately."
)
OXYGEN_DEPLETION_MODAL_BODY = (
    "LIFE SUPPORT SYSTEMS OFFLINE!\n\n"
    "Oxygen levels dropping to critical levels.\n\n"
    "All crew are advised to evacuate or obtain emergency oxygen supplies immediately."
)
OXYGEN_DEPLETION_FOLLOWUP_TITLE = "CRITICAL SYSTEM ALERT"
OXYGEN_DEPLETION_FOLLOWUP_MESSAGE = (
    "STATION ALERT: Life support systems have been deactivated!\n\n"
    "Damage will begin in 15s unless life support is turned on."
)


def oxygen_damage_for_tick(life_support_level, elapsed_seconds):
    """Return integer oxygen damage for the elapsed interval at the given life support level.

    Damage scales from 1x at level 4 to 2x at level 0, in +0.25x steps.
    """
    if life_support_level > DAMAGE_THRESHOLD_LEVEL:
        return 0
    multiplier_x100 = 100 + 25 * (DAMAGE_THRESHOLD_LEVEL - life_support_level)
    periods = max(elapsed_seconds / float(OXYGEN_TICK_SECONDS), 0)
    return int((BASE_DAMAGE_PER_TICK * multiplier_x100 * periods) // 100)


def advance_oxygen_recovery_accumulator(player_data, elapsed_seconds):
    """Advance the shared recovery accumulator; return whole % to apply this tick."""
    timers = player_data.setdefault("damage_timers", {})
    recovery_acc = timers.get("oxygen_recovery_acc", 0.0) + (
        elapsed_seconds / float(RECOVERY_SECONDS_PER_PERCENT)
    )
    recovery_amount = int(recovery_acc)
    timers["oxygen_recovery_acc"] = recovery_acc - recovery_amount
    return recovery_amount


def recovery_floor_for(current_oxygen_damage):
    """Passive recovery floor: doctor required at/above 25%, else recover to 0."""
    return DOCTOR_REQUIRED_FLOOR if current_oxygen_damage >= DOCTOR_REQUIRED_FLOOR else 0


def life_support_entering_damage_range(previous, new):
    """True when life support drops from above the damage threshold into it."""
    return previous > DAMAGE_THRESHOLD_LEVEL and new <= DAMAGE_THRESHOLD_LEVEL


def _oxygen_depletion_grace_active(player_data, master_elapsed_seconds):
    """True if the post-emergency-announcement grace period is still running.

    Clears the timer once it expires so damage resumes normally afterward.
    """
    if master_elapsed_seconds is None:
        return False

    timers = player_data.get("damage_timers") or {}
    depletion = timers.get("oxygen_depletion")
    if not depletion or not depletion.get("active"):
        return False

    damage_starts_at = depletion.get("damage_starts_at_seconds")
    if damage_starts_at is None or master_elapsed_seconds >= damage_starts_at:
        depletion["active"] = False
        return False

    return True


def apply_oxygen_tick(player_data, station_crew, elapsed_seconds, master_elapsed_seconds=None):
    """Apply oxygen damage or recovery for one master clock tick.

    ``elapsed_seconds`` is the real-time delta since the previous tick (used
    to scale damage/recovery); ``master_elapsed_seconds`` is the current
    master game clock value, used only to check the oxygen-depletion grace
    period start/end.

    Mutates crew ``damage["oxygen"]``. Returns player-facing events for UI:
    ``{"crossed_warnings": [...], "died": bool, "life_support_level": int}``.
    """
    life_support_level = player_data["station_power"]["system_levels"].get("life_support", 10)
    events = {
        "crossed_warnings": [],
        "died": False,
        "life_support_level": life_support_level,
    }

    all_crew = [player_data] + list(station_crew)
    life_support_failing = life_support_level <= DAMAGE_THRESHOLD_LEVEL
    in_grace_period = life_support_failing and _oxygen_depletion_grace_active(
        player_data, master_elapsed_seconds
    )
    # During the grace period, oxygen holds steady: no damage, no recovery.
    apply_damage = life_support_failing and not in_grace_period
    apply_recovery = not life_support_failing

    oxygen_damage_rate = 0
    if apply_damage:
        oxygen_damage_rate = oxygen_damage_for_tick(life_support_level, elapsed_seconds)
        apply_damage = oxygen_damage_rate > 0

    recovery_amount = 0
    if apply_recovery:
        recovery_amount = advance_oxygen_recovery_accumulator(player_data, elapsed_seconds)

    for crew_member in all_crew:
        is_player = crew_member is player_data
        current_oxygen_damage = int(crew_member["damage"].get("oxygen", 0))

        if apply_damage and oxygen_damage_rate > 0:
            new_oxygen_damage = min(DEATH_THRESHOLD, current_oxygen_damage + oxygen_damage_rate)
            crew_member["damage"]["oxygen"] = new_oxygen_damage

            if is_player:
                for threshold in WARNING_THRESHOLDS:
                    if current_oxygen_damage < threshold <= new_oxygen_damage:
                        events["crossed_warnings"].append(threshold)
                        break
                if new_oxygen_damage >= DEATH_THRESHOLD:
                    events["died"] = True

        elif apply_recovery and current_oxygen_damage > 0 and recovery_amount > 0:
            floor = recovery_floor_for(current_oxygen_damage)
            if current_oxygen_damage > floor:
                new_oxygen_damage = max(floor, current_oxygen_damage - recovery_amount)
                crew_member["damage"]["oxygen"] = new_oxygen_damage

    return events


def apply_oxygen_death_state(player_data):
    """Apply soft-death state: oxygen/limbs reset and teleport to quarters. No UI."""
    player_data["damage"]["oxygen"] = POST_DEATH_OXYGEN
    for limb in player_data["limbs"]:
        player_data["limbs"][limb] = POST_DEATH_LIMB_HEALTH
    player_data["location"] = dict(donut.QUARTERS_LOCATION)
