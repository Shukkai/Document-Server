from datetime import datetime, timedelta, timezone
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

# ---------------- User, File & Folder tables ----------------
class User(db.Model, UserMixin):
    id          = db.Column(db.Integer, primary_key=True)
    username    = db.Column(db.String(256),  unique=True, nullable=False)
    email       = db.Column(db.String(256), unique=True)
    password_hash = db.Column(db.String(256),      nullable=False)
    grade       = db.Column(db.Integer, nullable=True)
    is_admin    = db.Column(db.Boolean, default=False)
    created_at  = db.Column(db.DateTime, server_default=db.func.now())

    files = db.relationship("File", backref="owner", lazy=True)
    folders = db.relationship("Folder", backref="owner", lazy=True)
    assigned_reviews = db.relationship("DocumentReview", foreign_keys="DocumentReview.reviewer_id", backref="reviewer", lazy=True)
    requested_reviews = db.relationship("DocumentReview", foreign_keys="DocumentReview.requester_id", backref="requester", lazy=True)
    notifications = db.relationship("Notification", backref="user", lazy=True)

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)


class Folder(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(255), nullable=False)
    owner_id    = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parent_id   = db.Column(db.Integer, db.ForeignKey('folder.id'), nullable=True)
    created_at  = db.Column(db.DateTime, server_default=db.func.now())

    parent = db.relationship('Folder', remote_side=[id], backref='subfolders')


class File(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    filename    = db.Column(db.String(255), nullable=False)
    mimetype    = db.Column(db.String(255))
    path        = db.Column(db.String(255))
    uploaded_at = db.Column(db.DateTime, server_default=db.func.now())
    owner_id    = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    folder_id   = db.Column(db.Integer, db.ForeignKey('folder.id'), nullable=True)
    current_version = db.Column(db.Integer, default=1)
    is_under_review = db.Column(db.Boolean, default=False)

    folder = db.relationship('Folder', backref='files')
    versions = db.relationship('FileVersion', backref='file', lazy=True, order_by='FileVersion.version_number.desc()', cascade='all, delete-orphan')
    reviews = db.relationship('DocumentReview', backref='file', lazy=True, cascade='all, delete-orphan')

    def get_latest_version(self):
        return FileVersion.query.filter_by(file_id=self.id).order_by(FileVersion.version_number.desc()).first()

    def get_version(self, version_number):
        return FileVersion.query.filter_by(file_id=self.id, version_number=version_number).first()

    def get_active_review(self):
        return DocumentReview.query.filter_by(file_id=self.id, status='pending').first()


class FileVersion(db.Model):
    id              = db.Column(db.Integer, primary_key=True)
    file_id         = db.Column(db.Integer, db.ForeignKey('file.id'), nullable=False)
    version_number  = db.Column(db.Integer, nullable=False)
    path            = db.Column(db.String(255), nullable=False)
    uploaded_at     = db.Column(db.DateTime, server_default=db.func.now())
    comment         = db.Column(db.String(500))  # Optional comment for version changes

    __table_args__ = (
        db.UniqueConstraint('file_id', 'version_number', name='unique_file_version'),
    )


# ---------------- Document Review System -----------------
class DocumentReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('file.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    requester_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(50), default='pending')  # 'pending', 'approved', 'rejected', 'cancelled'
    comments = db.Column(db.Text, nullable=True)
    requested_at = db.Column(db.DateTime, server_default=db.func.now())
    reviewed_at = db.Column(db.DateTime, nullable=True)
    original_version = db.Column(db.Integer, nullable=True)  # Version before changes
    modified_version = db.Column(db.Integer, nullable=True)  # Version with changes

    __table_args__ = (
        db.Index("ix_review_status", "status"),
        db.Index("ix_review_reviewer", "reviewer_id"),
        db.Index("ix_review_file", "file_id"),
    )


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), default='info')  # 'info', 'review_request', 'review_completed'
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    related_file_id = db.Column(db.Integer, db.ForeignKey('file.id'), nullable=True)
    related_review_id = db.Column(db.Integer, db.ForeignKey('document_review.id'), nullable=True)

    related_file = db.relationship('File', backref='notifications')
    related_review = db.relationship('DocumentReview', backref='notifications')

    __table_args__ = (
        db.Index("ix_notification_user", "user_id"),
        db.Index("ix_notification_read", "is_read"),
    )


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
