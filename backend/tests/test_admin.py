from io import BytesIO
from ..models import User, db

def _auth(client):
    client.post("/register", json={
        "username": "vuser", "email": "v@mail", "password": "pwd", "grade": 3
    })
    client.post("/login", json={"username": "vuser", "password": "pwd"})

def test_admin(client, app):
    _auth(client)

    # —— to admin ——
    with app.app_context():
        user = User.query.filter_by(username="vuser").first()
        user.is_admin = True
        db.session.commit()

    client.post("/logout")
    client.post("/login", json={"username": "vuser", "password": "pwd"})

    # register a new user
    rv = client.post("/register", json={
        "username": "u1",
        "email": "u1@mail",
        "password": "pwd",
        "grade": 1
    })

    # admin list users
    rv = client.get("/users")
    assert rv.status_code == 200
    users = rv.get_json()
    assert any(u["username"] == "u1" for u in users)
    uid = next(u["id"] for u in users if u["username"] == "u1")

    # admin get user files
    rv = client.get(f"/admin/user-files/{uid}")
    assert rv.status_code == 200
    files = rv.get_json()
    assert files["target_user"]["id"] == uid