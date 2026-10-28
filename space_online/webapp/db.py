"""SQLite storage: accounts and each account's single character save."""

import datetime
import json
import sqlite3

from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);

-- user_id is the primary key, so an account can never hold two characters.
CREATE TABLE IF NOT EXISTS characters (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    player_data TEXT NOT NULL,
    ui_state TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


def _now():
    return datetime.datetime.now().isoformat(timespec="seconds")


def get_db():
    if "db" not in g:
        # isolation_level=None: transactions are opened explicitly with BEGIN IMMEDIATE.
        g.db = sqlite3.connect(current_app.config["DATABASE"], timeout=15, isolation_level=None)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    with app.app_context():
        db = get_db()
        db.execute("PRAGMA journal_mode = WAL")
        db.executescript(SCHEMA)
        close_db()


def create_user(username, password_hash):
    """Insert an account. Returns the new id, or None if the username is taken."""
    try:
        cursor = get_db().execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, password_hash, _now()),
        )
    except sqlite3.IntegrityError:
        return None
    return cursor.lastrowid


def get_user_by_name(username):
    return get_db().execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()


def get_user(user_id):
    return get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def character_summary(user_id):
    """Name/job/credits of the account's character, or None if it has none."""
    row = get_db().execute(
        "SELECT player_data, created_at, updated_at FROM characters WHERE user_id = ?", (user_id,)
    ).fetchone()
    if row is None:
        return None
    player_data = json.loads(row["player_data"])
    return {
        "name": player_data.get("name"),
        "job": player_data.get("job"),
        "credits": player_data.get("credits", 0),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def insert_character(user_id, player_data, ui_state):
    """Store a new character. Returns False if the account already has one."""
    now = _now()
    try:
        get_db().execute(
            "INSERT INTO characters (user_id, player_data, ui_state, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, json.dumps(player_data), json.dumps(ui_state), now, now),
        )
    except sqlite3.IntegrityError:
        return False
    return True


def delete_character(user_id):
    get_db().execute("DELETE FROM characters WHERE user_id = ?", (user_id,))


def update_character(user_id, fn):
    """Load, mutate, and save a character atomically.

    fn(player_data, ui_state) -> (result, player_data, ui_state). Returns
    result, or None if the account has no character. BEGIN IMMEDIATE
    serializes concurrent requests (e.g. a poll racing a click) so neither
    overwrites the other's changes.
    """
    db = get_db()
    db.execute("BEGIN IMMEDIATE")
    try:
        row = db.execute(
            "SELECT player_data, ui_state FROM characters WHERE user_id = ?", (user_id,)
        ).fetchone()
        if row is None:
            db.execute("ROLLBACK")
            return None
        result, player_data, ui_state = fn(json.loads(row["player_data"]), json.loads(row["ui_state"]))
        db.execute(
            "UPDATE characters SET player_data = ?, ui_state = ?, updated_at = ? WHERE user_id = ?",
            (json.dumps(player_data), json.dumps(ui_state), _now(), user_id),
        )
        db.execute("COMMIT")
        return result
    except Exception:
        db.execute("ROLLBACK")
        raise
