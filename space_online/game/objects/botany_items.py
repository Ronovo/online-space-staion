"""Botany seed/liquid/tool item definitions and growth-class timers."""

BOTANY_SEED_IDS = (
    "tomato_seeds",
    "potato_seeds",
    "wheat_seeds",
    "carrot_seeds",
    "apple_seeds",
)

BOTANY_LIQUID_TOOL_IDS = (
    "watering_can",
    "miracle_grow",
    "plentiful_harvest",
    "the_ooze_mutagen",
    "trowel",
    "chainsaw",
)

BOTANY_VEND_IDS = BOTANY_SEED_IDS + BOTANY_LIQUID_TOOL_IDS

GROWTH_STAGES = 5  # 1..5, mature at 5

GROWTH_CLASS_SECONDS = {
    "crop": 3 * 60,
    "fruiting": 5 * 60,
    "tree": 8 * 60,
}

GROWTH_STAGE_LABELS = {
    1: "Seedling",
    2: "Sprouting",
    3: "Growing",
    4: "Ripening",
    5: "Mature",
}

# Floor so Miracle Grow's speed bonus can never shrink a stage to ~0 seconds.
MIN_STAGE_SECONDS = 30

# Miracle Grow shortens each stage's duration by this fraction. Non-stacking:
# applying it again just keeps the bonus at this value.
MIRACLE_GROW_SPEED_BONUS = 0.1

# Plentiful Harvest multiplies produce quantity on the next harvest.
PLENTIFUL_HARVEST_YIELD_MULTIPLIER = 3

BOTANY_ITEMS = {
    "tomato_seeds": {
        "id": "tomato_seeds",
        "name": "Tomato Seeds",
        "description": "Grows into juicy red tomatoes.",
        "category": "Botany",
        "attributes": {
            "produces": "tomato",
            "plant_name": "Tomato",
            "growth_class": "fruiting",
            "vend_kinds": ["seed"],
        },
        "actions": ["examine", "equip", "drop"],
    },
    "potato_seeds": {
        "id": "potato_seeds",
        "name": "Potato Seeds",
        "description": "Produces starchy potatoes.",
        "category": "Botany",
        "attributes": {
            "produces": "potato",
            "plant_name": "Potato",
            "growth_class": "crop",
            "vend_kinds": ["seed"],
        },
        "actions": ["examine", "equip", "drop"],
    },
    "wheat_seeds": {
        "id": "wheat_seeds",
        "name": "Wheat Seeds",
        "description": "Grows into tall wheat stalks.",
        "category": "Botany",
        "attributes": {
            "produces": "wheat",
            "plant_name": "Wheat",
            "growth_class": "crop",
            "vend_kinds": ["seed"],
        },
        "actions": ["examine", "equip", "drop"],
    },
    "carrot_seeds": {
        "id": "carrot_seeds",
        "name": "Carrot Seeds",
        "description": "Produces orange root vegetables.",
        "category": "Botany",
        "attributes": {
            "produces": "carrot",
            "plant_name": "Carrot",
            "growth_class": "crop",
            "vend_kinds": ["seed"],
        },
        "actions": ["examine", "equip", "drop"],
    },
    "apple_seeds": {
        "id": "apple_seeds",
        "name": "Apple Seeds",
        "description": "Grows into small apple trees.",
        "category": "Botany",
        "attributes": {
            "produces": "apple",
            "plant_name": "Apple",
            "growth_class": "tree",
            "vend_kinds": ["seed"],
        },
        "actions": ["examine", "equip", "drop"],
    },
    "watering_can": {
        "id": "watering_can",
        "name": "Watering Can",
        "description": "A sturdy can for watering hydroponic planters.",
        "category": "Botany",
        "attributes": {
            "vend_kinds": ["liquid", "tool"],
        },
        "actions": ["examine", "equip", "drop"],
    },
    "miracle_grow": {
        "id": "miracle_grow",
        "name": "Miracle Grow",
        "description": "A potent liquid fertilizer for healthier plants.",
        "category": "Botany",
        "attributes": {
            "vend_kinds": ["liquid"],
        },
        "actions": ["examine", "equip", "drop"],
    },
    "plentiful_harvest": {
        "id": "plentiful_harvest",
        "name": "Plentiful Harvest",
        "description": "A growth serum that promises larger yields.",
        "category": "Botany",
        "attributes": {
            "vend_kinds": ["liquid"],
        },
        "actions": ["examine", "equip", "drop"],
    },
    "the_ooze_mutagen": {
        "id": "the_ooze_mutagen",
        "name": '"The Ooze" Mutagen',
        "description": "An unstable green mutagen. Handle with care.",
        "category": "Botany",
        "attributes": {
            "vend_kinds": ["liquid"],
        },
        "actions": ["examine", "equip", "drop"],
    },
    "trowel": {
        "id": "trowel",
        "name": "Trowel",
        "description": "A small hand tool for digging and transplanting.",
        "category": "Botany",
        "attributes": {
            "vend_kinds": ["tool"],
        },
        "actions": ["examine", "equip", "drop"],
    },
    "chainsaw": {
        "id": "chainsaw",
        "name": "Chainsaw",
        "description": "A powered saw for clearing stubborn plant growth.",
        "category": "Botany",
        "attributes": {
            "vend_kinds": ["tool"],
        },
        "actions": ["examine", "equip", "drop"],
    },
}


def growth_duration_seconds(growth_class):
    """Return seconds per stage advance for a growth class (defaults to crop)."""
    return GROWTH_CLASS_SECONDS.get(growth_class, GROWTH_CLASS_SECONDS["crop"])


def effective_stage_seconds(growth_class, miracle_grow=0.0):
    """Seconds per stage advance after Miracle Grow's speed bonus (floored)."""
    base = growth_duration_seconds(growth_class)
    boosted = base * (1 - float(miracle_grow or 0.0))
    return max(MIN_STAGE_SECONDS, boosted)


def compute_growth_stage(planted_at_seconds, growth_class, elapsed_seconds, miracle_grow=0.0):
    """Return growth stage 1..5 from planted time vs master clock.

    GROWTH_CLASS_SECONDS is time spent on each stage before advancing.
    Mature (stage 5) after (GROWTH_STAGES - 1) intervals. miracle_grow
    (0.0 by default, 0.1 once applied) shortens each stage's duration.
    """
    if planted_at_seconds is None:
        return 1
    stage_len = effective_stage_seconds(growth_class, miracle_grow)
    elapsed = max(0.0, float(elapsed_seconds) - float(planted_at_seconds))
    return min(GROWTH_STAGES, 1 + int(elapsed / stage_len))


def growth_stage_label(stage):
    """Display label for a growth stage."""
    try:
        stage = int(stage)
    except (TypeError, ValueError):
        stage = 1
    return GROWTH_STAGE_LABELS.get(stage, "Growing")


def growth_seconds_to_next_stage(planted_at_seconds, growth_class, elapsed_seconds, miracle_grow=0.0):
    """Seconds until the next stage advance, or 0 if mature / missing data."""
    if planted_at_seconds is None:
        return 0
    stage = compute_growth_stage(planted_at_seconds, growth_class, elapsed_seconds, miracle_grow)
    if stage >= GROWTH_STAGES:
        return 0
    stage_len = effective_stage_seconds(growth_class, miracle_grow)
    elapsed = max(0.0, float(elapsed_seconds) - float(planted_at_seconds))
    next_at = stage * stage_len
    return max(0, int(next_at - elapsed))


def refresh_planter_growth(planter, elapsed_seconds):
    """Update an occupied planter's cached growth_stage from the game clock.

    Applies Miracle Grow's speed bonus and the watering-can survival rule: if
    a stage tries to advance while the planter hasn't been watered since its
    last advance, the plant dies and growth freezes at its last stage.

    Returns the current stage (0 if empty).
    """
    if not planter or not planter.get("occupied"):
        return 0
    if planter.get("dead"):
        return int(planter.get("growth_stage") or 1)

    planted_at_seconds = planter.get("planted_at_seconds")
    if planted_at_seconds is None:
        return int(planter.get("growth_stage") or 1)

    miracle_grow = float(planter.get("miracle_grow") or 0.0)
    raw_stage = compute_growth_stage(
        planted_at_seconds, planter.get("growth_class"), elapsed_seconds, miracle_grow
    )
    previous_stage = int(planter.get("growth_stage") or 1)

    if raw_stage > previous_stage:
        if not planter.get("watered"):
            planter["dead"] = True
            planter["growth_stage"] = previous_stage
            return previous_stage
        planter["growth_stage"] = raw_stage
        if raw_stage < GROWTH_STAGES:
            # A further cycle remains; water is used up and must be reapplied.
            planter["watered"] = False
        return raw_stage

    planter["growth_stage"] = raw_stage
    return raw_stage


def refresh_all_planters_growth(player_data, elapsed_seconds=None):
    """Refresh growth_stage on all botany planters. Returns the planters list."""
    from space_online.game.helper_methods.game_clock import get_elapsed_seconds

    if elapsed_seconds is None:
        elapsed_seconds = get_elapsed_seconds(player_data)
    botany = player_data.get("botany") or {}
    planters = botany.get("planters") or []
    for planter in planters:
        refresh_planter_growth(planter, elapsed_seconds)
    return planters
