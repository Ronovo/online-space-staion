import base64
import time
from urllib.parse import parse_qs, urlsplit

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from tests.conftest import post, register

KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
PUBLIC_KEY = base64.b64encode(KEY.public_key().public_bytes(Encoding.DER, PublicFormat.SubjectPublicKeyInfo)).decode()


def issue(sub, aud="space-online", expires_in=300):
    now = int(time.time())
    return jwt.encode({"iss": "ronovo", "aud": aud, "sub": sub, "name": f"player{sub}", "iat": now,
                       "exp": now + expires_in}, KEY, algorithm="RS256")


@pytest.fixture
def ronovo(monkeypatch):
    monkeypatch.setenv("RONOVO_SSO_URL", "http://ronovo.test")
    monkeypatch.setenv("RONOVO_SSO_PUBLIC_KEY", PUBLIC_KEY)


def ronovo_login(client, sub, token=None):
    query = parse_qs(urlsplit(client.get("/sso/login").location).query)
    assert query["app"] == ["space-online"]
    return client.post("/sso/callback", data={"state": query["state"][0], "token": token or issue(sub)})


def test_ronovo_login_is_off_without_config(client, monkeypatch):
    monkeypatch.delenv("RONOVO_SSO_URL", raising=False)
    assert b"Log In with Ronovo" not in client.get("/login").data
    assert client.get("/sso/login").status_code == 404


def test_first_login_makes_an_account_that_every_device_shares(ronovo, app):
    phone = app.test_client()
    assert b"Log In with Ronovo" in phone.get("/login").data
    res = ronovo_login(phone, "1")
    assert res.status_code == 302 and res.location.endswith("/character/new")
    res = post(phone, "/character/new", name="Ava", department="Engineering", job="Engineer")
    assert res.status_code == 302 and res.location.endswith("/play")

    laptop = app.test_client()
    res = ronovo_login(laptop, "1")
    assert res.status_code == 302 and res.location.endswith("/")
    with laptop.session_transaction() as session:
        assert session["username"] == "player1"
    assert b"Ava" in laptop.get("/").data


def test_a_taken_name_gets_a_number(ronovo, app):
    register(app.test_client(), "player2")
    client = app.test_client()
    ronovo_login(client, "2")
    with client.session_transaction() as session:
        assert session["username"] == "player22"


def test_ronovo_accounts_have_no_usable_password(ronovo, app):
    client = app.test_client()
    ronovo_login(client, "4")
    post(client, "/logout")
    res = post(client, "/login", username="player4", password="")
    assert res.status_code == 200 and b"Incorrect username or password" in res.data


@pytest.mark.parametrize("token", [issue("1", aud="casino"), issue("1", expires_in=-10)])
def test_bad_tokens_are_refused(ronovo, client, token):
    assert ronovo_login(client, "1", token).status_code == 400


def test_callback_needs_the_state_from_this_browser(ronovo, client):
    client.get("/sso/login")
    assert client.post("/sso/callback", data={"state": "wrong", "token": issue("1")}).status_code == 400
