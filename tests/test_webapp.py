from helpers import act, create_character, post, register


def test_home_requires_login(client):
    response = client.get("/")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_register_logs_in_and_goes_to_character_creation(client):
    response = register(client)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/character/new")


def test_register_rejects_invalid_username(client):
    response = register(client, username="x")
    assert response.status_code == 200
    assert b"Usernames are 3-32 characters" in response.data


def test_register_rejects_mismatched_passwords(client):
    response = post(client, "/register", username="pilot", password="hunter22", confirm_password="other22")
    assert b"Passwords do not match." in response.data


def test_register_rejects_taken_username(client, app):
    register(client)
    response = register(app.test_client(), username="PILOT")
    assert b"That username is already taken." in response.data


def test_login_with_wrong_password_fails(client):
    register(client)
    post(client, "/logout")
    response = post(client, "/login", username="pilot", password="wrong-password")
    assert b"Incorrect username or password." in response.data


def test_login_and_logout(client):
    register(client)
    post(client, "/logout")
    response = post(client, "/login", username="pilot", password="hunter22")
    assert response.headers["Location"].endswith("/character/new")
    create_character(client)
    post(client, "/logout")
    response = post(client, "/login", username="pilot", password="hunter22")
    assert response.headers["Location"].endswith("/")
    response = post(client, "/logout")
    assert response.headers["Location"].endswith("/login")
    assert client.get("/").status_code == 302


def test_post_without_csrf_token_is_rejected(client):
    response = client.post("/register", data={"username": "pilot", "password": "hunter22",
                                             "confirm_password": "hunter22"})
    assert response.status_code == 400


def test_character_creation_rejects_job_outside_department(client):
    register(client)
    response = create_character(client, department="Civilian", job="Captain")
    assert response.status_code == 200
    assert b"Please select a job." in response.data


def test_create_character_and_play(client):
    register(client)
    response = create_character(client)
    assert response.headers["Location"].endswith("/play")
    response = client.get("/play")
    assert response.status_code == 200
    assert client.get("/character/new").headers["Location"].endswith("/play")


def test_act_tick_returns_screen_and_skips_unchanged_html(client):
    register(client)
    create_character(client)

    first = act(client, action="tick").get_json()
    assert {"hash", "title", "alerts", "choice", "html"} <= first.keys()

    second = act(client, action="tick", hash=first["hash"]).get_json()
    assert ("html" in second) == (second["hash"] != first["hash"])


def test_act_args_that_are_not_an_object_are_ignored(client):
    register(client)
    create_character(client)
    response = act(client, action="game.move", args=["north"])
    assert response.status_code == 200
    assert "redirect" not in response.get_json()


def test_act_without_character_redirects_to_creation(client):
    register(client)
    assert act(client, action="tick").get_json()["redirect"].endswith("/character/new")


def test_delete_character_needs_confirmation(client):
    register(client)
    create_character(client)
    response = post(client, "/character/delete")
    assert response.headers["Location"].endswith("/")
    assert client.get("/play").status_code == 200

    response = post(client, "/character/delete", confirm="yes")
    assert response.headers["Location"].endswith("/character/new")
    assert client.get("/play").headers["Location"].endswith("/character/new")


def test_progress_persists_across_logins(client):
    register(client)
    create_character(client, name="Persistent Pat")
    post(client, "/logout")
    post(client, "/login", username="pilot", password="hunter22")
    assert b"Persistent Pat" in client.get("/").data
