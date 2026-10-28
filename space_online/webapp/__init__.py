"""Flask web front end for Space Station Explorer."""

import functools
import hashlib
import os
import re
import secrets

from flask import (
    Flask,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from space_online.game.character_methods.character_creation import (
    JOBS,
    NPC_NAMES,
    SELECT_DEPARTMENT,
    SELECT_JOB,
    create_character,
    group_jobs_by_department,
)
from space_online.game.helper_methods.ui_panels import default_ui_state
from space_online.game.main import SpaceStationGame
from space_online.webapp import db

USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{3,32}$")
MIN_PASSWORD_LENGTH = 6
MAX_PASSWORD_LENGTH = 128


def _load_secret_key(instance_path):
    """SPACE_ONLINE_SECRET_KEY env var, else a key generated once into the instance folder."""
    env_key = os.environ.get("SPACE_ONLINE_SECRET_KEY")
    if env_key:
        return env_key
    key_path = os.path.join(instance_path, "secret_key")
    if not os.path.exists(key_path):
        with open(key_path, "w", encoding="utf-8") as f:
            f.write(secrets.token_hex(32))
    with open(key_path, encoding="utf-8") as f:
        return f.read().strip()


def create_app(test_config=None):
    app = Flask(__name__, instance_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "instance"))
    os.makedirs(app.instance_path, exist_ok=True)
    app.config.update(
        DATABASE=os.path.join(app.instance_path, "space_online.sqlite3"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    if test_config:
        app.config.update(test_config)
    if not app.config.get("SECRET_KEY"):
        app.config["SECRET_KEY"] = _load_secret_key(app.instance_path)

    app.teardown_appcontext(db.close_db)
    db.init_db(app)
    _register_routes(app)
    return app


def _csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)
    return session["csrf_token"]


def _check_csrf():
    sent = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token")
    if not sent or not secrets.compare_digest(sent, session.get("csrf_token", "")):
        abort(400, description="Invalid or missing CSRF token. Reload the page and try again.")


def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("user_id") is None or db.get_user(session["user_id"]) is None:
            session.clear()
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def _run_game(user_id, action=None, args=None):
    """Tick the character's clock, apply one action, save, and return the view (or None)."""
    def run(player_data, ui_state):
        game = SpaceStationGame(player_data, ui_state)
        game.tick()
        if action:
            game.perform(action, args or {})
        view = game.view()
        return view, game.to_save_data(), game.ui
    return db.update_character(user_id, run)


def _render_screen(view):
    html = render_template("game/screen.html", view=view)
    return html, hashlib.sha1(html.encode("utf-8")).hexdigest()[:16]


def _register_routes(app):
    @app.context_processor
    def inject_globals():
        return {"csrf_token": _csrf_token, "current_user": session.get("username")}

    @app.before_request
    def protect_posts():
        if request.method == "POST":
            _check_csrf()

    @app.route("/")
    @login_required
    def home():
        return render_template("home.html", character=db.character_summary(session["user_id"]))

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            confirm = request.form.get("confirm_password", "")
            error = None
            if not USERNAME_PATTERN.match(username):
                error = "Usernames are 3-32 characters: letters, numbers, dot, dash, or underscore."
            elif not MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH:
                error = f"Passwords must be {MIN_PASSWORD_LENGTH}-{MAX_PASSWORD_LENGTH} characters."
            elif password != confirm:
                error = "Passwords do not match."
            else:
                user_id = db.create_user(username, generate_password_hash(password))
                if user_id is None:
                    error = "That username is already taken."
                else:
                    session.clear()
                    session["user_id"] = user_id
                    session["username"] = username
                    return redirect(url_for("new_character"))
            flash(error, "error")
            return render_template("register.html", username=username)
        return render_template("register.html", username="")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            user = db.get_user_by_name(username)
            if user is None or not check_password_hash(user["password_hash"], request.form.get("password", "")):
                flash("Incorrect username or password.", "error")
                return render_template("login.html", username=username)
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("home"))
        return render_template("login.html", username="")

    @app.route("/logout", methods=["POST"])
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.route("/character/new", methods=["GET", "POST"])
    @login_required
    def new_character():
        if db.character_summary(session["user_id"]) is not None:
            return redirect(url_for("play"))

        form = {
            "name": request.form.get("name", ""),
            "department": request.form.get("department", SELECT_DEPARTMENT),
            "job": request.form.get("job", SELECT_JOB),
        }
        if request.method == "POST":
            try:
                player_data = create_character(form["name"], form["department"], form["job"])
            except ValueError as error:
                flash(str(error), "error")
            else:
                if not db.insert_character(session["user_id"], player_data, default_ui_state()):
                    flash("You already have a character.", "error")
                    return redirect(url_for("home"))
                return redirect(url_for("play"))

        return render_template(
            "create_character.html",
            form=form,
            departments=group_jobs_by_department(),
            jobs=JOBS,
            npc_names=NPC_NAMES,
            select_department=SELECT_DEPARTMENT,
            select_job=SELECT_JOB,
        )

    @app.route("/character/delete", methods=["POST"])
    @login_required
    def delete_character():
        if request.form.get("confirm") != "yes":
            flash("Tick the confirmation box to delete your character.", "error")
            return redirect(url_for("home"))
        db.delete_character(session["user_id"])
        flash("Your character has been deleted. All progress was lost.", "info")
        return redirect(url_for("new_character"))

    @app.route("/play")
    @login_required
    def play():
        view = _run_game(session["user_id"])
        if view is None:
            return redirect(url_for("new_character"))
        html, screen_hash = _render_screen(view)
        initial = {
            "hash": screen_hash,
            "title": view["title"],
            "alerts": view["alerts"],
            "choice": view["choice"],
        }
        return render_template("play.html", screen_html=html, initial_state=initial)

    @app.route("/api/act", methods=["POST"])
    @login_required
    def act():
        payload = request.get_json(silent=True) or {}
        action = payload.get("action")
        view = _run_game(
            session["user_id"],
            None if action == "tick" else action,
            payload.get("args"),
        )
        if view is None:
            return jsonify({"redirect": url_for("new_character")})
        if view["redirect"]:
            return jsonify({"redirect": url_for(view["redirect"])})

        html, screen_hash = _render_screen(view)
        response = {
            "hash": screen_hash,
            "title": view["title"],
            "alerts": view["alerts"],
            "choice": view["choice"],
        }
        if screen_hash != payload.get("hash"):
            response["html"] = html
        return jsonify(response)
