import os
import shutil
import tempfile
import pytest

# ✅ 設定測試用資料庫
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

# ✅ 正確引入 Flask 應用
from ..app import app as real_app, db

@pytest.fixture(scope="session")
def flask_app():
    tmp_dir = tempfile.mkdtemp()
    real_app.config.update(
        TESTING=True,
        UPLOAD_FOLDER=tmp_dir,
        WTF_CSRF_ENABLED=False,
    )
    with real_app.app_context():
        db.create_all()
        yield real_app
        db.session.remove()
        db.drop_all()
    shutil.rmtree(tmp_dir)

# ✅ pytest-flask 預期這個名字
@pytest.fixture(scope="session")
def app(flask_app):
    return flask_app

@pytest.fixture
def client(app):
    return app.test_client()
