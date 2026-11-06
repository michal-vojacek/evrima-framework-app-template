"""Shared fixtures, adapted from the framework's tests/conftest.py (docs/modules.md, section 10).

Apps are built from an explicit environment, never from the shell or .env.
The admin fixtures (add_admin, log_in, admin_client) are copied in once the
website has modules with admin screens.
"""

import pytest

from evrima.db import migrations

from mysite import create_app

# SQLite in memory and in-process rate limits: the suite needs neither
# PostgreSQL nor Redis.
BASE_ENV = {
    "EVRIMA_ENV": "testing",
    "SECRET_KEY": "test-secret-key-" + "x" * 32,
    "DATABASE_URL": "sqlite://",
    "REDIS_URL": "memory://",
    "CONTACT_RECIPIENT": "enquiries@example.com",
}


@pytest.fixture
def make_app(tmp_path):
    """Return a builder for migrated testing apps of the website."""
    def build(env=None, **overrides):
        environ = {**BASE_ENV, "MEDIA_ROOT": str(tmp_path / "media"), **(env or {})}
        app = create_app(config_overrides=overrides or None, environ=environ)
        with app.app_context():
            migrations.upgrade()
        return app
    return build


@pytest.fixture
def app(make_app):
    """The website as a testing app."""
    return make_app()


def https_client(app):
    """Return a test client that talks HTTPS, so Secure cookies round-trip."""
    client = app.test_client()
    client.environ_base["wsgi.url_scheme"] = "https"
    return client


@pytest.fixture
def client(app):
    """An HTTPS test client for the website."""
    return https_client(app)
