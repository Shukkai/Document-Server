import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    
    UPLOAD_FOLDER = 'uploads'                          # Root uploads dir
    USER_ROOT_FOLDER = os.path.join(UPLOAD_FOLDER, 'users')  # /uploads/users/{user_id}/...

    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25 MB per upload

    USER_FOLDER_QUOTA_MB = 500             # Optional: 500 MB per user (soft limit)
    FOLDER_DEPTH_LIMIT = 10                # Optional: nested folder levels

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://flaskuser:flaskpass@host.docker.internal/cloud_docs"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_COOKIE_NAME = "session"
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False