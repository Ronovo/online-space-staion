"""Stock market simulation, master-timer cycles, and the quarters trading terminal."""

import random

from space_online.game.helper_methods.game_clock import get_elapsed_seconds
from space_online.game.helper_methods.ui_panels import panel_action, register_panel

DEFAULT_COMPANY_NAMES = [
    "TechCorp",
    "GlobalBank",
    "HealthCare Plus",
    "EnergyCo",
    "FoodChain",
    "AutoMakers",
    "RetailGiant",
    "PharmaTech",
    "RealEstate Co",
    "MediaGroup",
    "Aerospace Inc",
    "TechStart",
    "GreenEnergy",
    "DigitalBank",
    "SmartHome",
]

CYCLE_INTERVAL_SECONDS = 300  # a new cycle every 5 minutes of master game time

class Company:
    def __init__(self, name, starting_value):
        self.name = name
        self.current_value = starting_value
        self.previous_value = starting_value
        self.price_history = [starting_value]
        self.owned_shares = 0
        
    def update_value(self):
        self.previous_value = self.current_value
        
        change = random.uniform(-0.10, 0.10)
        
        self.current_value = max(1.0, self.current_value * (1 + change))
        
        self.price_history.append(self.current_value)
        
        if len(self.price_history) > 50:
            self.price_history.pop(0)


def create_default_companies(history_cycles=5):
    """Create the default company list with optional price history."""
    companies = [Company(name, random.uniform(10, 1000)) for name in DEFAULT_COMPANY_NAMES]
    for _ in range(history_cycles):
        for company in companies:
            company.update_value()
    return companies


def serialize_companies(companies):
    """Serialize live company objects for player_data storage."""
    return [
        {
            "name": company.name,
            "current_value": company.current_value,
            "previous_value": company.previous_value,
            "price_history": company.price_history,
        }
        for company in companies
    ]


def apply_companies_from_save(companies, company_data_list):
    """Restore live company objects from saved player_data."""
    for company, company_data in zip(companies, company_data_list, strict=True):
        company.name = company_data["name"]
        company.current_value = company_data["current_value"]
        company.previous_value = company_data["previous_value"]
        company.price_history = company_data["price_history"]


def sync_holdings_to_companies(companies, stock_holdings):
    """Sync player stock holdings onto company owned_shares fields."""
    holdings = stock_holdings or {}
    for company in companies:
        company.owned_shares = holdings.get(company.name, 0)


def get_seconds_until_next_cycle(elapsed_seconds, interval=CYCLE_INTERVAL_SECONDS):
    """Calculate seconds remaining until the next market cycle, per the master timer."""
    return int(max(0, interval - (elapsed_seconds % interval)))


def default_stock_market_state():
    """Return a fresh stock_market block for player_data."""
    return {
        "cycle_number": 1,
        "companies": [],
        "trade_log": [],
    }


def round_credits(value):
    """Credits are kept to the cent, rounded."""
    return round(value, 2)


def record_trade(player_data, cycle, side, company_name, shares, price, total):
    """Append or merge a buy/sell entry in the current cycle trade log."""
    if "stock_market" not in player_data:
        player_data["stock_market"] = {}

    if "trade_log" not in player_data["stock_market"]:
        player_data["stock_market"]["trade_log"] = []

    current_cycle_entry = None
    for entry in player_data["stock_market"]["trade_log"]:
        if entry.get("cycle") == cycle:
            current_cycle_entry = entry
            break

    if not current_cycle_entry:
        current_cycle_entry = {
            "cycle": cycle,
            "trades": {"bought": {}, "sold": {}},
        }
        player_data["stock_market"]["trade_log"].append(current_cycle_entry)

    if side not in current_cycle_entry["trades"]:
        current_cycle_entry["trades"][side] = {}

    side_trades = current_cycle_entry["trades"][side]
    if company_name in side_trades:
        existing = side_trades[company_name]
        existing["amount"] += shares
        existing["total"] += total
        existing["price"] = existing["total"] / existing["amount"]
    else:
        side_trades[company_name] = {
            "amount": shares,
            "price": price,
            "total": total,
        }


def generate_market_tip(companies_data):
    """Return a random overheard market tip, or None if no companies exist."""
    if not companies_data:
        return None

    company = random.choice(companies_data)
    direction = random.choice(["rise", "fall"])
    name = company["name"]

    if direction == "rise":
        return f"Overheard that {name} stock is expected to rise soon!"
    return f"Overheard that {name} stock might be dropping in value soon!"


class StockMarketEngine:
    """Owns live market state and master-timer-driven tick logic."""

    def __init__(self, companies=None):
        self.companies = companies if companies is not None else create_default_companies()
        self.cycle_number = 1

    def tick_if_due(self, elapsed_seconds):
        """Advance the market to match the master timer. Returns True if it changed.

        Cycles are scheduled purely off ``elapsed_seconds``: cycle N ends at
        ``N * CYCLE_INTERVAL_SECONDS``. Catches up fully (not just one cycle)
        if a lot of time passed since the last check, e.g. after loading a
        save that sat untouched for a while.
        """
        target_cycle = int(elapsed_seconds // CYCLE_INTERVAL_SECONDS) + 1
        if target_cycle <= self.cycle_number:
            return False

        while self.cycle_number < target_cycle:
            for company in self.companies:
                company.update_value()
            self.cycle_number += 1

        return True

    def sync_to_player_data(self, player_data):
        """Write current market state into player_data."""
        if "stock_market" not in player_data:
            player_data["stock_market"] = default_stock_market_state()

        sync_holdings_to_companies(self.companies, player_data.get("stock_holdings"))

        player_data["stock_market"].update({
            "cycle_number": self.cycle_number,
            "companies": serialize_companies(self.companies),
        })

        if "trade_log" not in player_data["stock_market"]:
            player_data["stock_market"]["trade_log"] = []

    @classmethod
    def from_player_data(cls, player_data):
        """Build an engine from the market state saved on player_data."""
        market_data = player_data.get("stock_market") or {}
        engine = cls(hydrate_companies(market_data.get("companies")))
        engine.cycle_number = market_data.get("cycle_number", 1)
        sync_holdings_to_companies(engine.companies, player_data.get("stock_holdings"))
        return engine


def hydrate_companies(companies):
    """Return live Company objects from Company instances or serialized dicts."""
    if not companies:
        return create_default_companies()
    if all(isinstance(company, Company) for company in companies):
        return list(companies)
    live = create_default_companies(history_cycles=0)
    apply_companies_from_save(live, companies)
    return live


FILTER_GROUPS = (
    ("filter", "Filter Stocks:", (("All", "Show All"), ("Affordable", "Affordable"), ("Expensive", "Expensive"))),
    ("sort", "Sort By Price:", (("price_asc", "Low to High"), ("price_desc", "High to Low"))),
    ("ownership", "Ownership:", (("all", "All Stocks"), ("owned", "Owned"), ("not_owned", "Not Owned"))),
    ("trend", "Trend:", (("all", "All"), ("rising", "Rising"), ("falling", "Falling"))),
)
FILTER_VALUES = {group: {value for value, _ in options} for group, _, options in FILTER_GROUPS}
SHARE_OPTIONS = (1, 5, 10, 25, 50, 100)

CHART_WIDTH = 560
CHART_HEIGHT = 300
CHART_MARGINS = (60, 16, 30, 44)  # left, right, top, bottom


def _market_filters(state):
    return {group: state.get(group, options[0][0]) for group, _, options in FILTER_GROUPS}


def _filtered_companies(companies, player_credits, filters):
    """Companies passing the affordability/ownership/trend filters, price-sorted."""
    listed = []
    for company in companies:
        can_afford = player_credits // company.current_value >= 1
        passes_affordability = (
            filters["filter"] == "All"
            or (filters["filter"] == "Affordable" and can_afford)
            or (filters["filter"] == "Expensive" and not can_afford)
        )

        is_owned = company.owned_shares > 0
        passes_ownership = (
            filters["ownership"] == "all"
            or (filters["ownership"] == "owned" and is_owned)
            or (filters["ownership"] == "not_owned" and not is_owned)
        )

        price_change = company.current_value - company.previous_value
        passes_trend = (
            filters["trend"] == "all"
            or (filters["trend"] == "rising" and price_change > 0)
            or (filters["trend"] == "falling" and price_change < 0)
        )

        if passes_affordability and passes_ownership and passes_trend:
            listed.append(company)

    listed.sort(key=lambda c: c.current_value, reverse=filters["sort"] == "price_desc")
    return listed


def _listed_and_selected(game, state):
    """Return (listed companies, selected company); selection falls back to the first row."""
    sync_holdings_to_companies(game.market_engine.companies, game.player_data.get("stock_holdings"))
    listed = _filtered_companies(
        game.market_engine.companies, game.player_data["credits"], _market_filters(state)
    )
    selected = next((c for c in listed if c.name == state.get("selected")), None)
    if selected is None and listed:
        selected = listed[0]
    return listed, selected


def _price_chart(company):
    """Polyline points and axis ticks for an inline SVG price-history chart."""
    prices = company.price_history
    left, right, top, bottom = CHART_MARGINS
    plot_w = CHART_WIDTH - left - right
    plot_h = CHART_HEIGHT - top - bottom
    low, high = min(prices), max(prices)
    if high == low:
        low, high = low - 1, high + 1
    span_x = max(1, len(prices) - 1)
    label_format = "{:.2f}" if high - low < 10 else "{:.0f}"

    def px(i):
        return left + plot_w * i / span_x

    def py(value):
        return top + plot_h * (1 - (value - low) / (high - low))

    return {
        "width": CHART_WIDTH,
        "height": CHART_HEIGHT,
        "left": left,
        "top": top,
        "right": CHART_WIDTH - right,
        "bottom": CHART_HEIGHT - bottom,
        "points": " ".join(f"{px(i):.1f},{py(v):.1f}" for i, v in enumerate(prices)),
        "color": "green" if prices[-1] >= prices[0] else "red",
        "y_ticks": [
            {"y": py(low + (high - low) * k / 4), "label": label_format.format(low + (high - low) * k / 4)}
            for k in range(5)
        ],
        "x_ticks": [{"x": px(i), "label": str(i)} for i in sorted({0, span_x // 2, span_x})],
        "title": f"{company.name} Price History",
    }


@register_panel("stock_market", "Stock Market")
def stock_market_panel(game, state):
    listed, selected = _listed_and_selected(game, state)
    credits = game.player_data["credits"]

    remaining = get_seconds_until_next_cycle(get_elapsed_seconds(game.player_data))
    if remaining <= 0:
        timer = {"text": "Updating Market...", "color": "green"}
    else:
        timer = {
            "text": f"Next Update: {remaining // 60:02d}:{remaining % 60:02d}",
            "color": "yellow" if remaining > 15 else "orange" if remaining > 5 else "red",
        }

    detail = None
    if selected is not None:
        price_change = selected.current_value - selected.previous_value
        detail = {
            "name": selected.name,
            "price": selected.current_value,
            "change": price_change,
            "change_pct": (price_change / selected.previous_value) * 100,
            "change_color": "green" if price_change >= 0 else "red",
            "owned": selected.owned_shares,
            "total_value": selected.owned_shares * selected.current_value,
            "max_buy": int(credits / selected.current_value),
            "max_sell": selected.owned_shares,
            "chart": _price_chart(selected),
        }

    return {
        "cycle": game.market_engine.cycle_number,
        "timer": timer,
        "credits": credits,
        "filter_groups": FILTER_GROUPS,
        "filters": _market_filters(state),
        "companies": [c.name for c in listed],
        "selected": selected.name if selected else None,
        "detail": detail,
        "share_options": SHARE_OPTIONS,
    }


@panel_action("stock_market")
def set_filter(game, state, args):
    group, value = args["group"], args["value"]
    if value in FILTER_VALUES.get(group, ()):
        state[group] = value


@panel_action("stock_market")
def select(game, state, args):
    name = str(args["name"])
    if any(company.name == name for company in game.market_engine.companies):
        state["selected"] = name


def _requested_shares(game, args):
    try:
        shares = int(str(args.get("shares", "")).strip())
    except ValueError:
        shares = 0
    if shares <= 0:
        game.alert("Input Error", "Please enter a valid number of shares.", kind="error")
        return None
    return shares


@panel_action("stock_market")
def buy(game, state, args):
    _, company = _listed_and_selected(game, state)
    shares = _requested_shares(game, args)
    if company is None or shares is None:
        return

    player_data = game.player_data
    total_cost = shares * company.current_value
    if total_cost > player_data["credits"]:
        game.alert("Transaction Failed", "Not enough credits for this purchase.", kind="error")
        return

    player_data["credits"] = round_credits(player_data["credits"] - total_cost)
    holdings = player_data.setdefault("stock_holdings", {})
    holdings[company.name] = holdings.get(company.name, 0) + shares
    record_trade(
        player_data, game.market_engine.cycle_number, "bought",
        company.name, shares, company.current_value, total_cost,
    )
    game.add_note(
        f"Bought {shares} shares of {company.name} "
        f"at {company.current_value:.2f} cr/share (Total: {total_cost:.2f} cr)"
    )
    state["selected"] = company.name
    game.alert(
        "Transaction Complete",
        f"Bought {shares} shares of {company.name} for {total_cost:.2f} credits.",
    )


@panel_action("stock_market")
def sell(game, state, args):
    _, company = _listed_and_selected(game, state)
    shares = _requested_shares(game, args)
    if company is None or shares is None:
        return

    player_data = game.player_data
    holdings = player_data.setdefault("stock_holdings", {})
    if shares > holdings.get(company.name, 0):
        game.alert("Transaction Failed", "You don't own that many shares.", kind="error")
        return

    total_value = shares * company.current_value
    player_data["credits"] = round_credits(player_data["credits"] + total_value)
    holdings[company.name] -= shares
    if holdings[company.name] <= 0:
        del holdings[company.name]
    record_trade(
        player_data, game.market_engine.cycle_number, "sold",
        company.name, shares, company.current_value, total_value,
    )
    game.add_note(
        f"Sold {shares} shares of {company.name} "
        f"at {company.current_value:.2f} cr/share (Total: {total_value:.2f} cr)"
    )
    state["selected"] = company.name
    game.alert(
        "Transaction Complete",
        f"Sold {shares} shares of {company.name} for {total_value:.2f} credits.",
    )


@panel_action("stock_market")
def history(game, state, args):
    game.open_panel("trade_history")


@register_panel("trade_history", "Trade History")
def trade_history_panel(game, state):
    trade_log = (game.player_data.get("stock_market") or {}).get("trade_log")
    return {"entries": list(reversed(trade_log)) if trade_log is not None else None}

