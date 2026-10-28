import sqlite3

from werkzeug.security import generate_password_hash

from tests.conftest import QUESTION, post, register


def reset(client, username, answer, password="newpass1"):
    return post(client, "/reset-password", username=username, answer=answer, password=password,
                confirm_password=password)


def test_register_needs_a_listed_question_and_an_answer(client):
    res = post(client, "/register", username="pilot", password="hunter22", confirm_password="hunter22",
               question="Favorite color?", answer="blue")
    assert b"Pick a security question" in res.data
    res = post(client, "/register", username="pilot", password="hunter22", confirm_password="hunter22",
               question=QUESTION, answer="   ")
    assert b"Answer your security question" in res.data


def test_the_right_answer_sets_a_new_password(client):
    register(client)
    post(client, "/logout")
    res = post(client, "/reset-password", username="pilot")
    assert QUESTION.replace("'", "&#39;").encode() in res.data
    assert b"That answer is wrong" in reset(client, "pilot", "cat").data
    res = reset(client, "pilot", "  REX ")
    assert res.status_code == 302 and res.location.endswith("/login")
    assert post(client, "/login", username="pilot", password="newpass1").status_code == 302


def test_wrong_answers_lock_resets(client):
    register(client)
    post(client, "/logout")
    for _ in range(5):
        reset(client, "pilot", "cat")
    assert b"Too many wrong answers" in reset(client, "pilot", "rex").data


def test_unknown_usernames_get_a_steady_stand_in_question(client):
    first = post(client, "/reset-password", username="ghost").data
    assert first == post(client, "/reset-password", username="ghost").data
    assert b"That answer is wrong" in reset(client, "ghost", "anything").data


def test_old_accounts_set_a_question_after_logging_in(app, client):
    db = sqlite3.connect(app.config["DATABASE"])
    db.execute("INSERT INTO users (username, password_hash, created_at) VALUES ('old', ?, 'now')",
               (generate_password_hash("hunter22"),))
    db.commit()
    db.close()
    res = post(client, "/login", username="old", password="hunter22")
    assert res.location.endswith("/security-question")
    res = post(client, "/security-question", question=QUESTION, answer="rex")
    assert res.status_code == 302 and res.location.endswith("/")
    post(client, "/logout")
    assert post(client, "/login", username="old", password="hunter22").location.endswith("/")
