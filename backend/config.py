import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 256 * 1024 * 1024  # 256 MB
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://flaskuser:flaskpass@host.docker.internal/cloud_docs"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_COOKIE_NAME = "session"
    SESSION_COOKIE_SAMESITE = "Lax"  # Or "None" if using HTTPS + different domains
    SESSION_COOKIE_SECURE = False    # Should be True if using HTTPS