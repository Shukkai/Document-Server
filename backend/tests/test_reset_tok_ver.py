from io import BytesIO
from datetime import datetime, timedelta, timezone

import pytest

# helper modules inside the same package
import backend.tests.test_auth as ta   # provides _register()
import backend.tests.test_version as tv  # provides _auth()

from ..models import User, db, generate_reset_token, verify_reset_token, FileVersion

# ---------------------------------------------------------------------------
# Reset‑token helpers (still uncovered elsewhere)
# ---------------------------------------------------------------------------

def test_reset_token_lifecycle(app):
    """Generate → verify → **expire** a reset token."""
    with app.app_context():
        u = User(username="tokuser", email="tok@ex", grade=1)
        u.set_password("x")
        db.session.add(u)
        db.session.commit()

        token = generate_reset_token(u, hours=0.01)  # ~4 s lifetime
        assert verify_reset_token(token).id == u.id

        # Force expiry with naive datetime
        rec = u.reset_tokens[0]
        rec.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        db.session.commit()
        assert verify_reset_token(token) is None



# ---------------------------------------------------------------------------
# Version flow using shared tv._auth helper (no duplication)
# ---------------------------------------------------------------------------

def test_admin_version_flow(client, app):
    """Full life‑cycle re‑using tv._auth to set up user & file."""
    tv._auth(client)  # registers vuser and logs in

    # v1 upload
    rv = client.post(
        "/upload",
        data={"file": (BytesIO(b"hello v1"), "note.txt")},
        content_type="multipart/form-data",
    )
    fid = rv.get_json()["file_id"]

    # edit → v2
    client.post(f"/file-content/{fid}", json={"content": "hello v2"})

    # elevate to admin
    with app.app_context():
        usr = User.query.filter_by(username="vuser").first()
        usr.is_admin = True
        db.session.commit()

    # refresh session
    client.post("/logout")
    client.post("/login", json={"username": "vuser", "password": "pwd"})

    # restore v1 → v3
    rv = client.post(f"/restore-version/{fid}/1")
    assert rv.status_code == 200
    assert rv.get_json()["new_version_number"] == 3

    # download v3
    rv = client.get(f"/download-version/{fid}/3")
    assert rv.status_code == 200

    # cleanup (retain only newest)
    rv = client.post(f"/cleanup-versions/{fid}")
    assert rv.status_code == 200

    with app.app_context():
        remaining = FileVersion.query.filter_by(file_id=fid).all()
        assert len(remaining) == 1 and remaining[0].version_number == 3
