import pytest

from space_online.webapp import create_app


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
