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

    # create sub-folder and delete it
    rv = client.post("/folders", json={"name": "docs2"})
    assert rv.status_code == 201
    folder_id2 = rv.get_json()["folder_id"]

    rv = client.delete(f"/folders/{folder_id2}")
    assert rv.status_code == 200
    assert rv.get_json()["message"] == "Folder deleted"

    # upload to root
    data = {"file": (BytesIO(b"hello world"), "note.txt")}
    rv = client.post("/upload", data=data,
                     content_type="multipart/form-data")
    assert rv.status_code == 201
    file_id = rv.get_json()["file_id"]

    # get file content
    rv = client.get(f"/file-content/{file_id}")
    assert rv.status_code == 200

    # move file into /docs
    rv = client.post("/move-file",
                     json={"file_id": file_id,
                           "target_folder_id": folder_id})
    assert rv.status_code == 200

    # move wrong file
    rv = client.post("/move-file",
                     json={"file_id": 9999,  # non-existent file
                           "target_folder_id": folder_id})
    assert rv.status_code == 404

    rv = client.post("/move-file",
                     json={"file_id": file_id,
                           "target_folder_id": 9999})  # non-existent folder
    assert rv.status_code == 404

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

    # permanently delete file
    rv = client.delete(f"/permanently-delete/{file_id}")
    assert rv.status_code == 200
    assert rv.get_json()["message"] == "File and all its versions permanently deleted"

    # upload to root and download it
    data = {"file": (BytesIO(b"hello world"), "note2.txt")}
    rv = client.post("/upload", data=data,
                     content_type="multipart/form-data")
    assert rv.status_code == 201
    file_id = rv.get_json()["file_id"]

    rv = client.get(f"/download/{file_id}")
    assert rv.status_code == 200