import pytest

from space_online.webapp import create_app
from ronovo_portfolio_auth.security_questions import QUESTIONS

CSRF = "test-csrf-token"


@pytest.fixture
def make_app(tmp_path):
    def build(**config):
        return create_app({
            "TESTING": True,
            "SECRET_KEY": "test",
            "DATABASE": str(tmp_path / "space_online.sqlite3"),
            **config,
        })
    return build


@pytest.fixture
def app(make_app):
    return make_app()


@pytest.fixture
def client(app):
    return app.test_client()


def set_csrf(client):
    # Login, register and logout clear the session, so the token is put back before every post.
    with client.session_transaction() as session:
        session["csrf_token"] = CSRF


def post(client, url, **data):
    set_csrf(client)
    return client.post(url, data={"csrf_token": CSRF, **data})


def act(client, **payload):
    set_csrf(client)
    return client.post("/api/act", json=payload, headers={"X-CSRF-Token": CSRF})


QUESTION = QUESTIONS[0]


def register(client, username="pilot", password="hunter22"):
    return post(client, "/register", username=username, password=password, confirm_password=password,
                question=QUESTION, answer="rex")


def create_character(client, name="Ada", department="Civilian", job="Staff Assistant"):
    return post(client, "/character/new", name=name, department=department, job=job)
