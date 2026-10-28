"""Food item definitions."""

FOOD_ITEMS = {
    "snack": {
        "id": "snack",
        "name": "Snack",
        "description": "A packaged station snack from a vending machine.",
        "category": "Food",
        "attributes": {},
        "actions": ["examine", "eat", "drop"],
    },
    "energy_bar": {  # From random event
        "id": "energy_bar",
        "name": "Energy Bar",
        "description": "A dense, nutrient-rich bar. Tastes like cardboard.",
        "category": "Food",
        "attributes": {},
        "actions": ["examine", "eat", "drop"],
    },
    "emergency_rations": {  # From locker
        "id": "emergency_rations",
        "name": "Emergency Rations",
        "description": "Standard emergency food supply. Use only when necessary.",
        "category": "Food",
        "attributes": {},
        "actions": ["examine", "eat", "drop"],
    },
}

PRODUCE = {
    "tomato": {
        "id": "tomato",
        "name": "Tomato",
        "description": "A juicy red tomato fresh from the hydroponics bay.",
        "category": "Food",
        "attributes": {},
        "actions": ["examine", "eat", "drop"],
    },
    "potato": {
        "id": "potato",
        "name": "Potato",
        "description": "A starchy potato grown on the station.",
        "category": "Food",
        "attributes": {},
        "actions": ["examine", "eat", "drop"],
    },
    "wheat": {
        "id": "wheat",
        "name": "Wheat",
        "description": "A bundle of tall wheat stalks.",
        "category": "Food",
        "attributes": {},
        "actions": ["examine", "eat", "drop"],
    },
    "carrot": {
        "id": "carrot",
        "name": "Carrot",
        "description": "An orange root vegetable from the botany lab.",
        "category": "Food",
        "attributes": {},
        "actions": ["examine", "eat", "drop"],
    },
    "apple": {
        "id": "apple",
        "name": "Apple",
        "description": "A crisp apple from a small hydroponic tree.",
        "category": "Food",
        "attributes": {},
        "actions": ["examine", "eat", "drop"],
    },
}

FOOD_ITEMS.update(PRODUCE)
