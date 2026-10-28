"""Hallway random-event catalog, trigger, and effect helpers."""

import random

from space_online.game.helper_methods.npc_movement import find_hall_passersby
from space_online.game.helper_methods.stock_market import generate_market_tip
from space_online.game.objects.drinks import DRINKS_MENU
from space_online.game.objects.items import ALL_ITEMS, add_to_inventory, get_item_definition

HALLWAY_EVENT_CHANCE = 0.20
EVENT_CATEGORIES = ("good", "neutral", "bad", "job")

STAFF_ASSISTANT_REQUESTS = [
    "The Botanist needs water for the planters.",
    "The Captain needs a hand in Engineering.",
    "The Bartender needs an ingredient for a drink.",
    "The Doctor needs someone to restock bandages.",
    "Security needs help filing paperwork.",
]

CAPTAIN_REQUESTS = [
    "Medbay requests authorization for emergency surgery supplies.",
    "Engineering needs approval to divert power to life support.",
    "Security requests permission to lock down a sector.",
    "A department head wants a private briefing.",
    "Cargo bay reports a missing shipment and needs orders.",
]


def ensure_job_event(player_data):
    """Set job_event_key from the player's current job (create / load / job change)."""
    job = player_data.get("job")
    if job:
        player_data["job_event_key"] = job
    else:
        player_data.pop("job_event_key", None)


def maybe_trigger_hallway_event(game):
    """Roll for a hallway event and trigger one on success."""
    if random.random() < HALLWAY_EVENT_CHANCE:
        trigger_random_event(game)


def _static_events(game):
    """Good / neutral / bad hallway events (job events are built separately)."""
    return [
        {
            "type": "good",
            "title": "Found Credits",
            "desc": "You found some credits on the floor!",
            "effect": lambda: add_credits(game, random.randint(50, 200)),
        },
        {
            "type": "good",
            "title": "Supply Crate",
            "desc": "You found an unsealed supply crate with useful items.",
            "effect": lambda: add_random_item(game),
        },
        {
            "type": "good",
            "title": "Market Tip",
            "desc": "You overheard a reliable market tip.",
            "effect": lambda: add_market_knowledge(game),
        },
        {
            "type": "neutral",
            "title": "Lost Tourist",
            "desc": (
                "A confused visitor asks for directions to the bar, "
                "then wanders off the wrong way."
            ),
            "effect": lambda: None,
        },
        {
            "type": "neutral",
            "title": "Recycled Air Whiff",
            "desc": (
                "The vents kick on with a blast of recycled air that smells "
                "faintly of coolant and coffee."
            ),
            "effect": lambda: None,
        },
        {
            "type": "neutral",
            "title": "Graffiti Tag",
            "desc": (
                "Someone has scratched a crude smiley into the wall paneling. "
                "Maintenance will be thrilled."
            ),
            "effect": lambda: None,
        },
        {
            "type": "neutral",
            "title": "Announcement",
            "desc": "The station PA system makes an announcement.",
            "effect": lambda: station_announcement(game),
        },
        {
            "type": "neutral",
            "title": "Bot Moves By",
            "desc": "A station bot rolls past you in the hallway.",
            "effect": lambda: bot_moves_by(game),
        },
        {
            "type": "neutral",
            "title": "Vending Machine Malfunction",
            "desc": "A nearby vending machine sputters and flashes error lights.",
            "effect": lambda: vending_machine_malfunction(game),
        },
        {
            "type": "bad",
            "title": "Lost Credits",
            "desc": (
                "You dropped some credits and couldn't find them all. "
                "You bumped your head looking for them."
            ),
            "effect": lambda: combined_effect(
                [
                    lambda: lose_credits(game, random.randint(10, 50)),
                    lambda: damage_limb(game, "head", 5, 10),
                ]
            ),
        },
        {
            "type": "bad",
            "title": "Small Explosion",
            "desc": "A nearby conduit explodes, showering you with hot sparks and debris!",
            "effect": lambda: combined_effect(
                [
                    lambda: damage_random_limb(game, 10, 25),
                    lambda: add_burn_damage(game, 5, 15),
                ]
            ),
        },
        {
            "type": "bad",
            "title": "Slip and Fall",
            "desc": "You slipped on a wet floor and fell hard.",
            "effect": lambda: damage_random_limb(game, 10, 20),
        },
        {
            "type": "bad",
            "title": "Steam Leak",
            "desc": "A pipe bursts, releasing scalding steam that burns your arm!",
            "effect": lambda: combined_effect(
                [
                    lambda: damage_limb(game, "left_arm", 5, 10),
                    lambda: add_burn_damage(game, 15, 30),
                ]
            ),
        },
        {
            "type": "bad",
            "title": "Falling Debris",
            "desc": "A ceiling panel breaks loose and hits your head!",
            "effect": lambda: damage_limb(game, "head", 15, 35),
        },
        {
            "type": "bad",
            "title": "Maintenance Accident",
            "desc": "Your leg gets caught in an open floor grate!",
            "effect": lambda: damage_limb(game, "right_leg", 10, 20),
        },
        {
            "type": "bad",
            "title": "Chemical Spill",
            "desc": "You walk through a chemical spill! Your leg is burned and you feel ill.",
            "effect": lambda: combined_effect(
                [
                    lambda: damage_limb(game, "left_leg", 5, 10),
                    lambda: add_burn_damage(game, 5, 15),
                    lambda: add_poison_damage(game, 10, 20),
                ]
            ),
        },
    ]


def _juice_fruit_names():
    """Fruit names derived from juice entries on the bar menu."""
    fruits = []
    for name in DRINKS_MENU:
        if name.endswith(" Juice"):
            fruits.append(name[: -len(" Juice")])
    return fruits


def _non_admin_jobs():
    from space_online.game.character_methods.character_creation import JOBS

    return [
        job
        for job, info in JOBS.items()
        if info.get("department") != "Administration"
    ]


def build_job_event(game):
    """Build the single job-category event for the player's current role."""
    ensure_job_event(game.player_data)
    job = game.player_data.get("job_event_key")
    if not job:
        return None

    if job == "Head of Personnel":
        crew = getattr(game, "station_crew", None) or game.player_data.get("station_crew", [])
        candidates = [npc for npc in crew if npc.get("name") and not npc.get("in_jail")]
        if not candidates:
            return None
        npc = random.choice(candidates)
        requested_job = random.choice(_non_admin_jobs())
        requester = npc.get("name", "A crew member")
        desc = (
            f"{requester} ({npc.get('job', 'Crew')}) has submitted an access request "
            f"to become {requested_job}. Review it at the HoP Access Control console."
        )

        def effect():
            game.player_data["access_request"] = {
                "requested_job": requested_job,
                "requester_name": requester,
            }
            game.add_note(
                f"Access request: {requester} requested assignment as {requested_job}."
            )

        return {
            "type": "job",
            "title": "Access Request",
            "desc": desc,
            "effect": effect,
        }

    if job == "Staff Assistant":
        request = random.choice(STAFF_ASSISTANT_REQUESTS)
        desc = f"Job request: {request}"

        def effect():
            game.add_note(desc)

        return {
            "type": "job",
            "title": "Job Request",
            "desc": desc,
            "effect": effect,
        }

    if job == "Engineer":
        desc = (
            "The solar panels have shut down unexpectedly. "
            "They must be restarted from the Engineering Panel."
        )

        def effect():
            power = game.player_data.setdefault("station_power", {})
            power["solar_charging"] = False
            game.add_note("Solar arrays went offline and need to be restarted.")

        return {
            "type": "job",
            "title": "Solar Panels Offline",
            "desc": desc,
            "effect": effect,
        }

    if job == "Doctor":
        desc = "Someone needs healing!"

        def effect():
            game.add_note("Job event: Someone needs healing! (stub)")

        return {
            "type": "job",
            "title": "Someone Needs Healing!",
            "desc": desc,
            "effect": effect,
        }

    if job == "Bartender":
        desc = "Someone requested a drink."

        def effect():
            game.add_note("Job event: Someone requested a drink. (stub)")

        return {
            "type": "job",
            "title": "Drink Request",
            "desc": desc,
            "effect": effect,
        }

    if job == "Botanist":
        fruits = _juice_fruit_names()
        if not fruits:
            return None
        fruit = random.choice(fruits)
        article = "an" if fruit[0].lower() in "aeiou" else "a"
        desc = f"The Bartender needs {article} {fruit.lower()} for juice."

        def effect():
            game.add_note(f"Bartender requested {fruit.lower()} for juice.")

        return {
            "type": "job",
            "title": "Juice Fruit Request",
            "desc": desc,
            "effect": effect,
        }

    if job == "Security Guard":
        crew = getattr(game, "station_crew", None) or game.player_data.get("station_crew", [])
        passersby = find_hall_passersby(game.player_data, crew)
        if passersby:
            culprit = random.choice(passersby)
            name = culprit.get("name", "A crew member")
            desc = f"You witness a crime! {name} is involved."
            note = f"Witnessed a crime involving {name}."
        else:
            desc = "You witness a crime! You do not catch who it is."
            note = "Witnessed a crime; perpetrator unidentified."

        def effect():
            game.add_note(note)

        return {
            "type": "job",
            "title": "Witness a Crime",
            "desc": desc,
            "effect": effect,
        }

    if job == "Captain":
        request = random.choice(CAPTAIN_REQUESTS)
        desc = f"Command request: {request}"

        def effect():
            game.add_note(desc)

        return {
            "type": "job",
            "title": "Command Request",
            "desc": desc,
            "effect": effect,
        }

    return None


def _events_by_category(game):
    """Group static events by type and attach the player's job event."""
    by_type = {category: [] for category in EVENT_CATEGORIES}
    for event in _static_events(game):
        by_type.setdefault(event["type"], []).append(event)

    job_event = build_job_event(game)
    if job_event is not None:
        by_type["job"].append(job_event)

    return by_type


def trigger_random_event(game):
    """Pick a category, then an event in that category, and show a combined popup."""
    by_type = _events_by_category(game)
    available = [cat for cat in EVENT_CATEGORIES if by_type.get(cat)]
    if not available:
        return

    category = random.choice(available)
    # If job was chosen but empty (should be rare), fall back to another category.
    if category == "job" and not by_type["job"]:
        fallback = [cat for cat in ("good", "neutral", "bad") if by_type.get(cat)]
        if not fallback:
            return
        category = random.choice(fallback)

    event = random.choice(by_type[category])

    game.event_messages = []
    try:
        event["effect"]()
        body = event["desc"]
        if game.event_messages:
            body = body + "\n\n" + "\n".join(game.event_messages)
        game.alert(event["title"], body)
    finally:
        game.event_messages = None


def _report_effect(game, title, message):
    """Show an effect popup, or buffer the message during a random event."""
    if game.event_messages is not None:
        game.event_messages.append(message)
    else:
        game.report(title, message)


def _add_damage_type(game, damage_key, label, min_damage, max_damage):
    damage = random.randint(min_damage, max_damage)
    original_damage = game.player_data["damage"].get(damage_key, 0)
    game.player_data["damage"][damage_key] = min(100, original_damage + damage)
    total = game.player_data["damage"][damage_key]
    _report_effect(
        game,
        f"{label} Damage",
        f"You suffered {damage}% {label.lower()} damage! Total {label.lower()} damage: {total}%.",
    )
    game.add_note(
        f"Suffered {label.lower()} damage: Took {damage}% damage (total now {total}%)"
    )


def add_burn_damage(game, min_damage, max_damage):
    _add_damage_type(game, "burn", "Burn", min_damage, max_damage)


def add_poison_damage(game, min_damage, max_damage):
    _add_damage_type(game, "poison", "Poison", min_damage, max_damage)


def combined_effect(effect_functions):
    for effect_fn in effect_functions:
        effect_fn()


def damage_random_limb(game, min_damage, max_damage):
    limb = random.choice(list(game.player_data["limbs"].keys()))
    damage_limb(game, limb, min_damage, max_damage)


def damage_limb(game, limb, min_damage, max_damage):
    if limb in game.player_data["limbs"]:
        damage = random.randint(min_damage, max_damage)

        original_health = game.player_data["limbs"][limb]
        game.player_data["limbs"][limb] = max(0, original_health - damage)

        limb_name = limb.replace("_", " ").title()

        _report_effect(
            game,
            "Blunt Injury",
            f"Your {limb_name} took {damage}% blunt damage and is now at {game.player_data['limbs'][limb]}%.",
        )

        game.add_note(
            f"Suffered blunt damage to {limb_name}: Took {damage}% damage "
            f"(from {original_health}% to {game.player_data['limbs'][limb]}%)"
        )


def add_credits(game, amount):
    game.player_data["credits"] += amount
    _report_effect(game, "Credits Added", f"You gained {amount} credits.")
    game.add_note(
        f"Found {amount} credits. New balance: {game.player_data['credits']} credits."
    )


def lose_credits(game, amount):
    old_credits = game.player_data["credits"]
    game.player_data["credits"] = max(0, old_credits - amount)
    _report_effect(game, "Credits Lost", f"You lost {amount} credits.")
    game.add_note(
        f"Lost {amount} credits. New balance: {game.player_data['credits']} credits."
    )


def add_random_item(game):
    """Add a random item (using item definitions) to the player's inventory."""
    available_item_ids = list(ALL_ITEMS.keys())

    if not available_item_ids:
        game.alert("Error", "No items defined to be found.", kind="warning")
        return

    item_id = random.choice(available_item_ids)

    item_def = get_item_definition(item_id)

    if not item_def:
        game.alert("Error", f"Could not find definition for random item ID: {item_id}", kind="error")
        return

    game.player_data.setdefault("inventory", [])

    add_to_inventory(game.player_data, item_def)
    item_name = item_def.get("name", "an item")
    _report_effect(
        game,
        "Item Found",
        f"You found {item_name} and added it to your inventory.",
    )

    game.add_note(f"Found {item_name} ({item_id}) and added it to inventory.")


def add_market_knowledge(game):
    """Add market knowledge to the player - reveals a tip about a stock."""
    message = generate_market_tip(game.player_data["stock_market"].get("companies", []))
    if message is None:
        _report_effect(
            game,
            "Market Tip",
            "You heard a stock tip, but don't understand the market yet.",
        )
        return

    _report_effect(game, "Market Tip", message)
    game.add_note(f"Market Tip: {message}")


def station_announcement(game):
    """Display a random station announcement."""
    announcements = [
        "Reminder to all crew: safety protocols must be followed at all times.",
        "The cafeteria is now serving special meal rations.",
        "Maintenance is scheduled in Sector 7 shortly.",
        "All personnel are reminded to report suspicious activity to security.",
        "The crew meeting is postponed until further notice.",
        "Environmental controls are being recalibrated. Expect minor temperature fluctuations.",
    ]

    announcement = random.choice(announcements)
    _report_effect(
        game,
        "Station Announcement",
        f"The PA system crackles: '{announcement}'",
    )


def heal_limb(game, limb, min_heal, max_heal):
    if limb not in game.player_data["limbs"]:
        return

    amount = random.randint(min_heal, max_heal)
    original = game.player_data["limbs"][limb]
    game.player_data["limbs"][limb] = min(100, original + amount)
    new_health = game.player_data["limbs"][limb]
    limb_name = limb.replace("_", " ").title()
    healed = new_health - original

    _report_effect(
        game,
        "Medical Treatment",
        f"Your {limb_name} was healed by {healed}% and is now at {new_health}%.",
    )
    game.add_note(
        f"Medical bot healed {limb_name}: +{healed}% "
        f"(from {original}% to {new_health}%)"
    )


def heal_damage_type(game, damage_key, label, min_heal, max_heal):
    amount = random.randint(min_heal, max_heal)
    original = game.player_data["damage"].get(damage_key, 0)
    game.player_data["damage"][damage_key] = max(0, original - amount)
    new_value = game.player_data["damage"][damage_key]
    healed = original - new_value

    _report_effect(
        game,
        "Medical Treatment",
        f"Your {label.lower()} damage was reduced by {healed}% "
        f"(now {new_value}%).",
    )
    game.add_note(
        f"Medical bot treated {label.lower()} damage: -{healed}% "
        f"(from {original}% to {new_value}%)"
    )


def medical_bot_heal(game):
    """Heal one random damaged limb or damage type by 5–10%."""
    candidates = []

    for limb, health in game.player_data.get("limbs", {}).items():
        if health < 100:
            candidates.append(("limb", limb))

    for damage_key, label in (("burn", "Burn"), ("poison", "Poison"), ("oxygen", "Oxygen")):
        if game.player_data.get("damage", {}).get(damage_key, 0) > 0:
            candidates.append(("damage", damage_key, label))

    if not candidates:
        _report_effect(
            game,
            "Medical Bot",
            "A medical bot scans you, finds nothing to treat, and rolls away.",
        )
        return

    choice = random.choice(candidates)
    if choice[0] == "limb":
        heal_limb(game, choice[1], 1, 5)
    else:
        heal_damage_type(game, choice[1], choice[2], 1, 5)


def bot_moves_by(game):
    """A maintenance, security, or medical bot passes by."""
    bot = random.choice(["maintenance", "security", "medical"])

    if bot == "maintenance":
        _report_effect(
            game,
            "Maintenance Bot",
            "A maintenance bot rolls past, scrubbing the floor as it goes.",
        )
    elif bot == "security":
        from space_online.game.helper_methods.jail import arrest_member, is_jailed

        if is_jailed(game.player_data):
            _report_effect(
                game,
                "Security Bot",
                "A security bot rolls past your cell without stopping.",
            )
        elif game.player_data.get("warrant", False):
            from space_online.game.helper_methods.jail import warrant_reason_text

            charge = warrant_reason_text(game.player_data)
            _report_effect(
                game,
                "Security Bot",
                "A security bot locks onto you. You are wanted — you are under arrest!\n"
                f"Charge: {charge}",
            )
            from space_online.game.helper_methods.game_clock import get_elapsed_seconds

            arrest_member(
                game.player_data,
                reason=(
                    "A security bot locks onto you. You are wanted — you are under arrest!\n"
                    f"Charge: {charge}"
                ),
                game=game,
                is_player=True,
                show_message=False,
                elapsed_seconds=get_elapsed_seconds(game.player_data),
            )
            game.add_note("Arrested by a security bot while wanted.")
        else:
            _report_effect(
                game,
                "Security Bot",
                "A security bot scans you briefly and continues on its patrol.",
            )
    else:
        _report_effect(
            game,
            "Medical Bot",
            "A medical bot stops beside you and runs a quick diagnostic.",
        )
        medical_bot_heal(game)


def add_snack(game):
    item_def = get_item_definition("snack")
    if not item_def:
        game.alert("Error", "Could not find definition for snack.", kind="error")
        return

    game.player_data.setdefault("inventory", [])
    add_to_inventory(game.player_data, item_def)
    _report_effect(
        game,
        "Free Snack",
        "You found a free Snack and added it to your inventory.",
    )
    game.add_note("Found a Snack from a vending machine and added it to inventory.")


def vending_machine_malfunction(game):
    """One of three vending machine outcomes."""
    outcome = random.choice(["spit_out", "stuck", "free_snack"])

    if outcome == "spit_out":
        _report_effect(
            game,
            "Vending Machine",
            "The machine violently spits something out at you!",
        )
        damage_random_limb(game, 1, 5)
    elif outcome == "stuck":
        _report_effect(
            game,
            "Vending Machine",
            "You see a snack stuck against the glass, just out of reach.",
        )
    else:
        _report_effect(
            game,
            "Vending Machine",
            "The machine clunks and a free snack drops into the tray.",
        )
        add_snack(game)
