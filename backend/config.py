import os
class Config:
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    SQLALCHEMY_DATABASE_URI = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://flaskuser:flaskpass@host.docker.internal/cloud_docs"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False