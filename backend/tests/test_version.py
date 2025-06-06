# tests/test_versions.py
from io import BytesIO
from ..models import User, db

def _auth(client):
    client.post("/register", json={
        "username": "vuser", "email": "v@mail", "password": "pwd", "grade": 3
    })
    client.post("/login", json={"username": "vuser", "password": "pwd"})

def test_save_generates_version_and_restore(client, app):
    _auth(client)

    # v1 upload
    rv = client.post("/upload",
                     data={"file": (BytesIO(b"v1"), "code.py")},
                     content_type="multipart/form-data")
    file_id = rv.get_json()["file_id"]

    # edit → v2
    rv = client.post(f"/file-content/{file_id}", json={"content": "print(2)"})
    assert rv.status_code == 200
    assert rv.get_json()["version"] == 2

    # get file version
    rv = client.get(f"/file-versions/{file_id}")
    assert rv.status_code == 200
    versions = rv.get_json()
    assert len(versions) == 2

    # —— 升級帳號為 admin ——
    with app.app_context():
        user = User.query.filter_by(username="vuser").first()
        user.is_admin = True
        db.session.commit()

    # 重新登入以刷新 session
    client.post("/logout")
    client.post("/login", json={"username": "vuser", "password": "pwd"})

    # restore v1 ⇒ 產生 v3
    rv = client.post(f"/restore-version/{file_id}/1")
    assert rv.status_code == 200
    assert rv.get_json()["new_version_number"] == 3

    # compare versions
    rv = client.get(f"/compare-versions/{file_id}/1/3")
    assert rv.status_code == 200

    # delete v2
    rv = client.delete(f"/delete-version/{file_id}/2")
    assert rv.status_code == 200
    assert rv.get_json()["message"] == "Version 2 deleted successfully"

    # upload version
    rv = client.post(f"/upload-version/{file_id}",
                     data={"file": (BytesIO(b"v3"), "code.py")},
                     content_type="multipart/form-data")
    assert rv.status_code == 201