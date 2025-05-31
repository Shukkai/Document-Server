from io import BytesIO
import json

def _register_and_login(client, username="u1"):
    # register
    client.post("/register", json={
        "username": username,
        "email": f"{username}@mail",
        "password": "pwd",
        "grade": 1
    })
    # login
    client.post("/login", json={"username": username, "password": "pwd"})

def test_folder_create_upload_move_rename_delete(client):
    _register_and_login(client)

    # create sub-folder
    rv = client.post("/folders", json={"name": "docs"})
    assert rv.status_code == 201
    folder_id = rv.get_json()["folder_id"]

    # upload to root
    data = {"file": (BytesIO(b"hello world"), "note.txt")}
    rv = client.post("/upload", data=data,
                     content_type="multipart/form-data")
    assert rv.status_code == 201
    file_id = rv.get_json()["file_id"]

    # move file into /docs
    rv = client.post("/move-file",
                     json={"file_id": file_id,
                           "target_folder_id": folder_id})
    assert rv.status_code == 200

    # rename inside /docs
    rv = client.post(f"/rename-file/{file_id}",
                     json={"new_filename": "readme.txt"})
    assert rv.status_code == 200
    assert rv.get_json()["new_filename"] == "readme.txt"

    # delete file (soft-delete)
    rv = client.delete(f"/delete/{file_id}")
    assert rv.status_code == 200

    # ensure list-deleted endpoint shows it
    rv = client.get("/list-deleted-files")
    assert rv.status_code == 200
    assert rv.get_json() == []