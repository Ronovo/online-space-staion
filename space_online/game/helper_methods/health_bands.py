"""The health and damage bands the character sheet, MedBay and station status all use."""


def health_band(value):
    """(status, colour) for a health percentage, where 100 is unhurt."""
    if value > 75:
        return "Healthy", "green"
    if value > 40:
        return "Injured", "yellow"
    return "Critical", "red"


def damage_band(value):
    """(status, colour) for a damage percentage, where 0 is unhurt."""
    if value < 10:
        return "Clear", "green"
    if value < 30:
        return "Mild", "yellow"
    if value < 60:
        return "Moderate", "orange"
    return "Severe", "red"
