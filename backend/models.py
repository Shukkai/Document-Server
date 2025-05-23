from datetime import datetime, timedelta, timezone
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

# ---------------- User & File tables ----------------
class User(db.Model, UserMixin):
    id          = db.Column(db.Integer, primary_key=True)
    username    = db.Column(db.String(64),  unique=True, nullable=False)
    email       = db.Column(db.String(128), unique=True)
    password_hash = db.Column(db.Text,      nullable=False)
    is_admin    = db.Column(db.Boolean, default=False)
    created_at  = db.Column(db.DateTime, server_default=db.func.now())

    files = db.relationship("File", backref="owner", lazy=True)

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)


class File(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    filename    = db.Column(db.String(255), nullable=False)
    mimetype    = db.Column(db.String(255))
    path        = db.Column(db.String(255))
    uploaded_at = db.Column(db.DateTime, server_default=db.func.now())
    owner_id    = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


# ---------------- Password-reset tokens -------------
class ResetToken(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token      = db.Column(db.String(128), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

    user = db.relationship("User", backref="reset_tokens")

    __table_args__ = (
        db.Index("ix_reset_token_token", "token"),
    )


# ---------------- Helpers ---------------------------
def generate_reset_token(user, hours: int = 1) -> str:
    """Create a one-time reset token that expires in *hours*."""
    raw = secrets.token_urlsafe(48)
    exp = datetime.now(timezone.utc) + timedelta(hours=hours)
    db.session.add(ResetToken(user_id=user.id, token=raw, expires_at=exp))
    db.session.commit()
    return raw


def verify_reset_token(token: str):
    """Return the User if token is valid and not expired, else None."""
    rec = ResetToken.query.filter_by(token=token).first()
    if rec and rec.expires_at > datetime.now(timezone.utc):
        return rec.user
    return None