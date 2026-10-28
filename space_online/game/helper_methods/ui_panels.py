"""Server-side UI state for the web client: panel stack, choices, and alerts.

The browser only renders what these structures describe. Panels are
full-screen overlays (only the top of the stack is visible), choices are
modal button prompts the player must answer, and alerts are one-shot
messages returned with the next response.
"""

import time

PANELS = {}
PANEL_ACTIONS = {}
CHOICE_HANDLERS = {}

_KIND_RANK = {"info": 0, "warning": 1, "error": 2}


def default_ui_state():
    return {"room_mode": "menu", "panels": [], "choices": []}


def register_panel(panel_type, title):
    """Register context_fn(game, state) -> dict, or None to auto-close the panel."""
    def decorator(context_fn):
        PANELS[panel_type] = {"title": title, "context": context_fn}
        return context_fn
    return decorator


def panel_action(panel_type, name=None):
    """Register fn(game, state, args) as an action of the top panel."""
    def decorator(fn):
        PANEL_ACTIONS[(panel_type, name or fn.__name__)] = fn
        return fn
    return decorator


def choice_handler(name):
    """Register fn(game, **args) run when the matching choice button is picked."""
    def decorator(fn):
        CHOICE_HANDLERS[name] = fn
        return fn
    return decorator


def set_feedback(state, text, color="cyan", seconds=3):
    """Show a panel feedback line; seconds=None keeps it until replaced."""
    state["feedback"] = {
        "text": text,
        "color": color,
        "until": time.time() + seconds if seconds else None,
    }


def current_feedback(state):
    feedback = state.get("feedback")
    if not feedback:
        return None
    until = feedback.get("until")
    if until is not None and time.time() >= until:
        state.pop("feedback", None)
        return None
    return feedback


def coalesce_reports(reports):
    """Merge reported (title, message, kind) tuples into one alert."""
    if len(reports) == 1:
        title, message, kind = reports[0]
        return {"title": title, "message": message, "kind": kind}

    unique_titles = {title for title, _, _ in reports}
    max_kind = max(reports, key=lambda r: _KIND_RANK.get(r[2], 0))[2]
    if len(unique_titles) == 1:
        title = next(iter(unique_titles))
        body = "\n\n".join(message for _, message, _ in reports)
    else:
        title = "Station Alerts"
        body = "\n\n".join(f"[{t}] {m}" for t, m, _ in reports)
    return {"title": title, "message": body, "kind": max_kind}
