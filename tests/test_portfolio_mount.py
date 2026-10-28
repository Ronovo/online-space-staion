import re

from flask import Flask
from werkzeug.middleware.dispatcher import DispatcherMiddleware

PREFIX = "/games/space-online"


def mounted_client(make_app):
    """The game mounted under a prefix the way the portfolio site mounts it."""
    game = make_app(SESSION_COOKIE_PATH=f"{PREFIX}/", BACK_LINK={"href": "/games", "label": "Games"})
    host = Flask("portfolio")
    host.wsgi_app = DispatcherMiddleware(host.wsgi_app, {PREFIX: game})
    return host.test_client()


def test_standalone_has_no_back_link(client):
    assert b'class="back"' not in client.get("/login").data


def test_mounted_pages_use_the_prefix_and_show_the_back_link(make_app):
    page = mounted_client(make_app).get(f"{PREFIX}/login").data
    assert b'href="/games"' in page
    assert f"{PREFIX}/static/icon.png".encode() in page


def test_mounted_register_stays_inside_the_prefix(make_app):
    client = mounted_client(make_app)
    page = client.get(f"{PREFIX}/register").get_data(as_text=True)
    token = re.search(r'name="csrf-token" content="([^"]+)"', page).group(1)
    response = client.post(f"{PREFIX}/register", data={
        "csrf_token": token, "username": "pilot", "password": "hunter22", "confirm_password": "hunter22",
    })
    assert response.status_code == 302
    assert response.headers["Location"].endswith(f"{PREFIX}/character/new")
    assert f"Path={PREFIX}/" in response.headers["Set-Cookie"]
