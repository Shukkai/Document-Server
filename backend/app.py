from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from models import db, File
from config import Config
import os
from werkzeug.utils import secure_filename
import time
from sqlalchemy.exc import OperationalError

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
CORS(app)
MAX_RETRIES = 10

@app.route('/')
def index():
    return {"message": "Flask backend is running."}

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    if not file:
        return {"error": "No file provided"}, 400

    filename = secure_filename(file.filename)
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(path)

    f = File(filename=filename, mimetype=file.mimetype, path=path)
    db.session.add(f)
    db.session.commit()

    return {"message": "Upload successful", "file_id": f.id}, 201

@app.route('/files', methods=['GET'])
def list_files():
    files = File.query.all()
    return jsonify([{"id": f.id, "name": f.filename} for f in files])

@app.route('/download/<int:file_id>', methods=['GET'])
def download_file(file_id):
    f = File.query.get_or_404(file_id)
    return send_from_directory(app.config['UPLOAD_FOLDER'], f.filename)

if __name__ == '__main__':
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

    for attempt in range(MAX_RETRIES):
        try:
            with app.app_context():
                db.create_all()
                print("✅ Database initialized.")
                break
        except OperationalError as e:
            print(f"⏳ MySQL not ready, retrying ({attempt + 1}/{MAX_RETRIES})...")
            time.sleep(3)
    else:
        print("❌ Failed to connect to MySQL after retries.")
        exit(1)

    app.run(host='0.0.0.0', port=5001)