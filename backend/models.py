from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    mimetype = db.Column(db.String(255))
    path = db.Column(db.String(255))
    uploaded_at = db.Column(db.DateTime, server_default=db.func.now())