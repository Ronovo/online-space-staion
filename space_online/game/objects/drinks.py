"""Drink definitions and the bartender mixer, recipe book, and ingredient panels."""

from space_online.game.helper_methods.ui_panels import panel_action, register_panel

DRINKS_MENU = {
    "Beer": {"price": 10, "alcohol_content": 1, "desc": "A refreshing glass of regular beer."},
    "Whiskey": {"price": 20, "alcohol_content": 2, "desc": "A shot of strong whiskey."},
    "Wine": {"price": 15, "alcohol_content": 2, "desc": "A fine glass of red wine."},
    "Vodka": {"price": 15, "alcohol_content": 2, "desc": "A shot of clear, strong vodka."},
    "Gin": {"price": 15, "alcohol_content": 2, "desc": "A botanical spirit with a distinctive flavor."},
    "Rum": {"price": 15, "alcohol_content": 2, "desc": "A sweet spirit distilled from sugarcane."},
    "Tequila": {"price": 18, "alcohol_content": 2, "desc": "A spirit made from the blue agave plant."},
    "Brandy": {"price": 22, "alcohol_content": 2, "desc": "A spirit distilled from wine or fermented fruit juice."},
    "Scotch": {"price": 25, "alcohol_content": 2, "desc": "A smoky whisky from Scotland."},
    "Orange Juice": {"price": 5, "desc": "A glass of fresh orange juice."},
    "Cranberry Juice": {"price": 5, "desc": "Tart and refreshing red juice."},
    "Pineapple Juice": {"price": 6, "desc": "Sweet tropical juice."},
    "Tonic Water": {"price": 4, "desc": "Carbonated water with quinine."},
    "Soda Water": {"price": 3, "desc": "Simple carbonated water."},
    "Cola": {"price": 4, "desc": "A sweet carbonated soft drink."},
    "Lemon Juice": {"price": 4, "desc": "Fresh, sour citrus juice."},
    "Lime Juice": {"price": 4, "desc": "Zesty green citrus juice."},
    "Grenadine": {"price": 5, "desc": "Sweet red syrup made from pomegranate."},
    "Water": {"price": 1, "desc": "A glass of water. Refreshing and healthy."},
}

MIXED_DRINKS = {
    "Screwdriver": {
        "ingredients": ["Vodka", "Orange Juice"],
        "price": 25,
        "alcohol_content": 2,
        "desc": "A classic mix of vodka and orange juice.",
    },
    "Gin and Tonic": {
        "ingredients": ["Gin", "Tonic Water"],
        "price": 20,
        "alcohol_content": 2,
        "desc": "A refreshing mix of gin and tonic water.",
    },
    "Rum and Cola": {
        "ingredients": ["Rum", "Cola"],
        "price": 20,
        "alcohol_content": 2,
        "desc": "A sweet mix of rum and cola.",
    },
    "Whiskey Sour": {
        "ingredients": ["Whiskey", "Lemon Juice", "Sugar"],
        "price": 28,
        "alcohol_content": 2,
        "desc": "A perfect balance of sour and sweet with whiskey.",
    },
    "Margarita": {
        "ingredients": ["Tequila", "Lime Juice", "Triple Sec"],
        "price": 30,
        "alcohol_content": 2,
        "desc": "A tangy, refreshing cocktail with a salt rim.",
    },
    "Bloody Mary": {
        "ingredients": ["Vodka", "Tomato Juice", "Hot Sauce", "Worcestershire Sauce"],
        "price": 28,
        "alcohol_content": 2,
        "desc": "A savory, spicy morning cocktail.",
    },
    "Mojito": {
        "ingredients": ["Rum", "Lime Juice", "Mint", "Sugar", "Soda Water"],
        "price": 32,
        "alcohol_content": 2,
        "desc": "A refreshing minty cocktail from Cuba.",
    },
    "Piña Colada": {
        "ingredients": ["Rum", "Coconut Cream", "Pineapple Juice"],
        "price": 30,
        "alcohol_content": 2,
        "desc": "A tropical blend that tastes like vacation.",
    },
    "Cosmopolitan": {
        "ingredients": ["Vodka", "Triple Sec", "Cranberry Juice", "Lime Juice"],
        "price": 30,
        "alcohol_content": 2,
        "desc": "A sophisticated, slightly tart cocktail.",
    },
    "Old Fashioned": {
        "ingredients": ["Whiskey", "Bitters", "Sugar", "Water"],
        "price": 32,
        "alcohol_content": 4,
        "desc": "A timeless cocktail that never goes out of style.",
    },
    "Negroni": {
        "ingredients": ["Gin", "Vermouth", "Campari"],
        "price": 30,
        "alcohol_content": 4,
        "desc": "A perfectly balanced bitter and sweet aperitif.",
    },
    "Manhattan": {
        "ingredients": ["Whiskey", "Vermouth", "Bitters"],
        "price": 32,
        "alcohol_content": 4,
        "desc": "A sophisticated whiskey cocktail.",
    },
    "Mai Tai": {
        "ingredients": ["Rum", "Lime Juice", "Orange Curacao", "Orgeat Syrup"],
        "price": 35,
        "alcohol_content": 4,
        "desc": "A complex tropical rum cocktail.",
    },
    "Daiquiri": {
        "ingredients": ["Rum", "Lime Juice", "Sugar"],
        "price": 28,
        "alcohol_content": 2,
        "desc": "A simple, refreshing rum cocktail.",
    },
    "Tom Collins": {
        "ingredients": ["Gin", "Lemon Juice", "Sugar", "Soda Water"],
        "price": 28,
        "alcohol_content": 2,
        "desc": "A refreshing gin cocktail served in a tall glass.",
    },
    "Singapore Sling": {
        "ingredients": ["Gin", "Cherry Brandy", "Pineapple Juice", "Lime Juice", "Grenadine"],
        "price": 35,
        "alcohol_content": 4,
        "desc": "A complex, fruity gin cocktail.",
    },
    "Between the Sheets": {
        "ingredients": ["Brandy", "Rum", "Triple Sec", "Lemon Juice"],
        "price": 35,
        "alcohol_content": 3,
        "desc": "A potent classic blending brandy, rum, orange, and lemon.",
    },
    "Suffering Bastard": {
        "ingredients": ["Brandy", "Gin", "Lime Juice", "Bitters", "Ginger Ale"],
        "price": 34,
        "alcohol_content": 3,
        "desc": "A sharp brandy and gin cocktail softened with ginger ale.",
    },
    "Boston Sidecar": {
        "ingredients": ["Brandy", "Rum", "Triple Sec", "Lime Juice"],
        "price": 34,
        "alcohol_content": 3,
        "desc": "A rum and brandy variation on the citrus-forward Sidecar.",
    },
    "Brass Monkey": {
        "ingredients": ["Vodka", "Rum", "Orange Juice"],
        "price": 30,
        "alcohol_content": 3,
        "desc": "A retro mix of vodka, rum, and orange juice.",
    },
    "Long Island Iced Tea": {
        "ingredients": ["Vodka", "Gin", "Rum", "Tequila", "Triple Sec", "Lemon Juice", "Cola"],
        "price": 40,
        "alcohol_content": 5,
        "desc": "A potent mix of multiple spirits with a cola finish.",
    },
    "Space Blaster": {
        "ingredients": ["Vodka", "Blue Curacao", "Sprite", "Lemon Juice"],
        "price": 35,
        "alcohol_content": 2,
        "desc": "A station specialty with an electric blue color.",
    },
    "Quantum Fizz": {
        "ingredients": ["Gin", "Lime Juice", "Sugar", "Mint", "Helium Gas"],
        "price": 38,
        "alcohol_content": 2,
        "desc": "A unique drink that temporarily changes your voice.",
    },
    "Nebula Cloud": {
        "ingredients": ["Whiskey", "Honey", "Dry Ice", "Cinnamon"],
        "price": 42,
        "alcohol_content": 2,
        "desc": "A smoky cocktail that mimics a space nebula.",
    },
    "Solar Flare": {
        "ingredients": ["Tequila", "Rum", "Pineapple Juice", "Lime Juice", "Grenadine"],
        "price": 36,
        "alcohol_content": 3,
        "desc": "A fiery tropical station special with a bright red glow.",
    },
}

SPIRITS = ["Vodka", "Gin", "Rum", "Whiskey", "Tequila", "Brandy", "Scotch"]
AVAILABLE_INGREDIENTS = SPIRITS + [
    "Orange Juice", "Cranberry Juice", "Pineapple Juice", "Tomato Juice",
    "Tonic Water", "Soda Water", "Water", "Cola", "Ginger Ale", "Sprite",
    "Lemon Juice", "Lime Juice", "Sugar", "Salt", "Honey",
    "Triple Sec", "Blue Curacao", "Orange Curacao", "Grenadine",
    "Bitters", "Vermouth", "Campari", "Cherry Brandy",
    "Mint", "Coconut Cream", "Hot Sauce", "Worcestershire Sauce",
    "Cinnamon", "Orgeat Syrup", "Dry Ice", "Helium Gas",
]

BASIC_RECIPES = ["Screwdriver", "Gin and Tonic", "Rum and Cola", "Whiskey Sour", "Daiquiri"]
SPECIAL_RECIPES = ["Space Blaster", "Quantum Fizz", "Nebula Cloud", "Solar Flare"]
MODIFIERS = [
    "Lemon Juice", "Lime Juice", "Sugar", "Salt", "Honey", "Triple Sec",
    "Blue Curacao", "Orange Curacao", "Grenadine", "Bitters", "Vermouth",
    "Campari", "Cherry Brandy",
]
BASIC_ALCOHOLIC_DRINKS = frozenset(SPIRITS) | {"Beer", "Wine"}


def is_drink_alcoholic(name, details):
    """Return True if the drink contains alcohol."""
    if name in DRINKS_MENU:
        return name in BASIC_ALCOHOLIC_DRINKS
    return any(ing in SPIRITS for ing in details.get("ingredients", []))


def _is_mixer(ingredient):
    return any(word in ingredient for word in ("Juice", "Water", "Cola", "Ale", "Sprite"))


def categorize_ingredients(ingredients=None):
    """Return (spirits, mixers, modifiers, specials) for the mixer UI."""
    ingredients = ingredients or AVAILABLE_INGREDIENTS
    spirits = [i for i in ingredients if i in SPIRITS]
    mixers = [i for i in ingredients if _is_mixer(i)]
    modifiers = [i for i in ingredients if i in MODIFIERS]
    specials = [i for i in ingredients if i not in spirits and i not in mixers and i not in modifiers]
    return spirits, mixers, modifiers, specials


def categorize_ingredients_exclusive(ingredients=None):
    """Return mutually exclusive (spirits, mixers, modifiers, specials) for display."""
    ingredients = sorted(ingredients or AVAILABLE_INGREDIENTS)
    spirits = []
    mixers = []
    modifiers = []
    specials = []

    for ingredient in ingredients:
        if ingredient in SPIRITS:
            spirits.append(ingredient)
        elif _is_mixer(ingredient):
            mixers.append(ingredient)
        elif ingredient in MODIFIERS:
            modifiers.append(ingredient)
        else:
            specials.append(ingredient)

    return spirits, mixers, modifiers, specials


def match_recipe(ingredients):
    """Return (drink_name, drink_data) if ingredients match a known recipe, else (None, None)."""
    sorted_ingredients = sorted(ingredients)
    for drink_name, drink_data in MIXED_DRINKS.items():
        if sorted_ingredients == sorted(drink_data["ingredients"]):
            return drink_name, drink_data
    return None, None


def get_mix_feedback(ingredients):
    """Return failure feedback for an unknown ingredient mix."""
    if len(ingredients) > 5:
        return "This has too many ingredients - most cocktails use 2-5 ingredients."
    if not any(item in SPIRITS for item in ingredients):
        return "Most mixed drinks need a spirit as the base (like Vodka, Rum, or Whiskey)."
    if all(item in SPIRITS for item in ingredients):
        return "This is just a mix of different spirits. Try adding some mixers or modifiers."
    return "This combination doesn't match any known recipe. Try a different mix."


def _mixer_categories():
    spirits, mixers, modifiers, specials = categorize_ingredients()
    return {
        "All": ("All Ingredients", AVAILABLE_INGREDIENTS),
        "Spirits": ("Spirits", spirits),
        "Mixers": ("Mixers", mixers),
        "Modifiers": ("Modifiers", modifiers),
        "Specials": ("Special Ingredients", specials),
    }


def _mixer_category(state):
    categories = _mixer_categories()
    key = state.get("category", "All")
    return key if key in categories else "All", categories


@register_panel("mixer", "Bartender's Drink Mixer")
def mixer_panel(game, state):
    key, categories = _mixer_category(state)
    heading, items = categories[key]
    return {
        "categories": list(categories),
        "category": key,
        "heading": f"--- {heading} ---",
        "ingredients": sorted(items),
        "selected_ingredient": state.get("selected_ingredient"),
        "glass": state.get("glass", []),
        "selected_glass": state.get("selected_glass"),
        "result": state.get("result"),
    }


@panel_action("mixer", "category")
def mixer_category(game, state, args):
    if args["name"] in _mixer_categories():
        state["category"] = args["name"]
        state.pop("selected_ingredient", None)


@panel_action("mixer")
def select_ingredient(game, state, args):
    if args["name"] in AVAILABLE_INGREDIENTS:
        state["selected_ingredient"] = args["name"]


MAX_GLASS_POURS = 10


@panel_action("mixer")
def add_ingredient(game, state, args):
    key, categories = _mixer_category(state)
    ingredient = state.get("selected_ingredient")
    glass = state.setdefault("glass", [])
    if len(glass) >= MAX_GLASS_POURS:
        game.alert("Mixer", "The glass is full.", kind="warning")
    elif ingredient in categories[key][1]:
        glass.append(ingredient)


@panel_action("mixer")
def select_glass(game, state, args):
    state["selected_glass"] = int(args["index"])


@panel_action("mixer")
def remove_ingredient(game, state, args):
    glass = state.setdefault("glass", [])
    index = state.pop("selected_glass", None)
    if index is not None and 0 <= index < len(glass):
        glass.pop(index)


@panel_action("mixer")
def clear_glass(game, state, args):
    state["glass"] = []
    state.pop("selected_glass", None)


@panel_action("mixer")
def mix(game, state, args):
    ingredients = state.get("glass", [])
    if not ingredients:
        state["result"] = {"text": "You need to add ingredients first!", "color": "white"}
        return

    drink_match, drink_data = match_recipe(ingredients)
    if drink_match:
        stock = game.player_data["bar_mixed_stock"]
        stock[drink_match] = stock.get(drink_match, 0) + 1
        state["result"] = {
            "text": (
                f"Success! You've mixed a {drink_match}.\n"
                f"{drink_data['desc']}\n"
                f"(Qty: {stock[drink_match]})"
            ),
            "color": "lightgreen",
        }
        game.add_note(f"Successfully mixed a {drink_match} at the bar.")
    else:
        state["result"] = {
            "text": f"You've created an unknown concoction. {get_mix_feedback(ingredients)}",
            "color": "red",
        }

    state["glass"] = []
    state.pop("selected_glass", None)


@panel_action("mixer")
def recipes(game, state, args):
    game.open_panel("recipes")


RECIPE_CATEGORIES = (
    ("all", "All Recipes"),
    ("basic", "Basic Recipes"),
    ("advanced", "Advanced Recipes"),
    ("special", "Station Specials"),
)


def _recipe_entry(drink_name):
    drink_data = MIXED_DRINKS[drink_name]
    return {
        "name": drink_name,
        "ingredients": ", ".join(drink_data["ingredients"]),
        "price": drink_data["price"],
        "desc": drink_data["desc"],
    }


def _advanced_recipes():
    return sorted(d for d in MIXED_DRINKS if d not in BASIC_RECIPES and d not in SPECIAL_RECIPES)


def _recipe_sections(category):
    basic = ("BASIC COCKTAILS", sorted(BASIC_RECIPES))
    advanced = ("ADVANCED COCKTAILS", _advanced_recipes())
    special = ("STATION SPECIALTIES", sorted(SPECIAL_RECIPES))
    chosen = {"basic": [basic], "advanced": [advanced], "special": [special]}.get(
        category, [basic, advanced, special]
    )
    return [
        {"title": title, "recipes": [_recipe_entry(d) for d in drinks]}
        for title, drinks in chosen
    ]


@register_panel("recipes", "Drink Recipes")
def recipes_panel(game, state):
    query = (state.get("query") or "").lower().strip()
    if not query:
        return {
            "categories": RECIPE_CATEGORIES,
            "header": "BARTENDER'S RECIPE BOOK",
            "sections": _recipe_sections(state.get("category", "all")),
            "query": "",
        }

    results = [
        _recipe_entry(name)
        for name, data in MIXED_DRINKS.items()
        if query in name.lower()
        or any(query in ingredient.lower() for ingredient in data["ingredients"])
        or query in data["desc"].lower()
    ]
    return {
        "categories": RECIPE_CATEGORIES,
        "header": f"SEARCH RESULTS FOR '{query}'",
        "sections": [{"title": None, "recipes": results}],
        "empty_message": None if results else "No recipes found matching your search.",
        "query": state.get("query", ""),
    }


@panel_action("recipes", "category")
def recipes_category(game, state, args):
    if args["name"] in dict(RECIPE_CATEGORIES):
        state["category"] = args["name"]
        state["query"] = ""


@panel_action("recipes")
def search(game, state, args):
    state["query"] = str(args.get("query", ""))[:100]


@panel_action("recipes")
def ingredients(game, state, args):
    game.open_panel("ingredients")


@register_panel("ingredients", "Available Ingredients")
def ingredients_panel(game, state):
    spirits, mixers, modifiers, specials = categorize_ingredients_exclusive()
    return {
        "sections": [
            ("SPIRITS", spirits),
            ("MIXERS", mixers),
            ("MODIFIERS", modifiers),
            ("SPECIAL INGREDIENTS", specials),
        ],
    }
