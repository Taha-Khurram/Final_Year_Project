"""
Shared pytest fixtures for the authentication test suite.

The real app talks to Firebase Auth + Firestore over the network. Tests must
never do that, so we:

  * pre-seed the Firebase singleton with a mock BEFORE any app code imports it
    (importing ``app.routes.auth`` instantiates ``FirestoreService()`` at module
    load, which calls ``FirebaseLoader.get_instance()``), and
  * build a *minimal* Flask app that mounts only the auth/user blueprints plus a
    stub ``blog.home`` endpoint, avoiding the scheduler and the heavy analytics
    blueprints entirely.
"""
import os
import sys
import json
import base64
from datetime import timedelta
from unittest.mock import MagicMock

import pytest

# --- Make the project root importable ---------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# --- Provide harmless env values that config.py reads at import time ---------
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("FIREBASE_SERVICE_ACCOUNT", "{}")

# --- Seed the Firebase singleton with a mock so nothing hits the network -----
from app.firebase.firebase_admin import FirebaseLoader  # noqa: E402

FirebaseLoader._instance = MagicMock(name="firestore_client")
FirebaseLoader._bucket = MagicMock(name="storage_bucket")


def make_fake_id_token(uid="test-uid", email="user@gmail.com"):
    """Build a fake 3-segment JWT whose payload decodes to the given claims.

    ``/api/auth/verify`` base64-decodes the middle segment itself to read the
    uid/email early; signature verification is mocked separately in tests, so
    only the payload segment needs to be real base64 JSON.
    """
    header = base64.urlsafe_b64encode(b'{"alg":"none"}').decode().rstrip("=")
    payload = base64.urlsafe_b64encode(
        json.dumps({"user_id": uid, "email": email}).encode()
    ).decode().rstrip("=")
    return f"{header}.{payload}.signature"


@pytest.fixture
def app():
    """A minimal Flask app mounting only the auth + user blueprints."""
    from flask import Flask, Blueprint
    from app.routes.auth import auth_bp
    from app.routes.user_mgmt import user_bp

    flask_app = Flask(__name__)
    flask_app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret-key",
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=15),
        FIREBASE_CONFIG={},
    )

    # Stub endpoint so url_for('blog.home') resolves inside the auth routes.
    blog = Blueprint("blog", __name__)

    @blog.route("/home")
    def home():
        return "home"

    flask_app.register_blueprint(blog)
    flask_app.register_blueprint(auth_bp)
    flask_app.register_blueprint(user_bp, url_prefix="/users")
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()
