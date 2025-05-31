def test_health(client):
    rv = client.get("/")
    assert rv.status_code == 200
    assert rv.get_json()["message"] == "Flask backend is running."

def test_register_and_login(client):
    rv = client.post("/register", json={
        "username": "alice",
        "email": "alice@mail.com",
        "password": "pwd123",
        "grade": 31
    })
    assert rv.status_code in (200, 201)

    rv = client.post("/login", json={
        "username": "alice",
        "password": "pwd123"
    })
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["message"] == "Login successful"
    assert data["user"]["username"] == "alice"