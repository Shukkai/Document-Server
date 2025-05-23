from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from models import db, File, User
from config import Config
import os
from werkzeug.utils import secure_filename
import time
from sqlalchemy.exc import OperationalError
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy import inspect

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.unauthorized_handler
def api_unauthorized():
    # Return JSON so the Vue app can handle auth state itself
    return jsonify({"error": "unauthenticated"}), 401

@login_manager.user_loader
def load_user(user_id):
    # SQLAlchemy 2.x: Session.get() replaces Query.get()
    return db.session.get(User, int(user_id))

CORS(app, supports_credentials=True)
MAX_RETRIES = 10

@app.route('/')
def index():
    return {"message": "Flask backend is running."}

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    file = request.files.get('file')
    if not file:
        return {"error": "No file provided"}, 400

    filename = secure_filename(file.filename)
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(path)

    f = File(filename=filename, mimetype=file.mimetype, path=path, owner_id=current_user.id)
    db.session.add(f)
    db.session.commit()

    return {"message": "Upload successful", "file_id": f.id}, 201

@app.route('/files', methods=['GET'])
@login_required
def list_files():
    files = File.query.filter_by(owner_id=current_user.id).all()
    return jsonify([{"id": f.id, "name": f.filename} for f in files])

@app.route('/download/<int:file_id>', methods=['GET'])
@login_required
def download_file(file_id):
    f = File.query.get_or_404(file_id)
    if f.owner_id != current_user.id and not getattr(current_user, "is_admin", False):
        return {"error": "Access denied"}, 403
    return send_from_directory(app.config['UPLOAD_FOLDER'], f.filename)

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if User.query.filter_by(username=data['username']).first():
        return {"error": "Username already exists"}, 400
    user = User(username=data['username'], email=data['email'])
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    return {"message": "Registered successfully."}

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if user and user.check_password(data['password']):
        login_user(user)
        return {"message": "Login successful"}
    return {"error": "Invalid credentials"}, 401

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return {"message": "Logged out"}

if __name__ == '__main__':
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    app.secret_key = os.environ.get("SECRET_KEY", "f2a7d9c1e3b64c6a8f901b8e5cbf97f3f90b3d1371e6a47e9c021c25c99c4ea1")
    for attempt in range(MAX_RETRIES):
        try:
            with app.app_context():
                db.create_all()
                inspector = inspect(db.engine)
                print("✅ Tables created:", inspector.get_table_names())
                break
        except OperationalError as e:
            print(f"⏳ MySQL not ready, retrying ({attempt + 1}/{MAX_RETRIES})...")
            time.sleep(3)
    else:
        print("❌ Failed to connect to MySQL after retries.")
        exit(1)

    app.run(host='0.0.0.0', port=5001)