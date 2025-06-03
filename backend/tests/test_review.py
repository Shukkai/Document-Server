def test_request_and_complete_review(client, flask_app):
    from io import BytesIO
    from ..models import User, db

    def _create_user(client, name):
        client.post("/register", json={
            "username": name, "email": f"{name}@mail", "password": "pwd", "grade":1
        })

    # requester & reviewer
    _create_user(client, "req")
    _create_user(client, "rev")

    # requester login + upload
    client.post("/login", json={"username":"req", "password":"pwd"})
    rv = client.post("/upload",
        data={"file": (BytesIO(b"draft"), "doc.txt")},
        content_type="multipart/form-data")
    file_id = rv.get_json()["file_id"]

    # lookup reviewer id
    with flask_app.app_context():
        reviewer_id = User.query.filter_by(username="rev").first().id

    # get list of reviewers for assigning
    rv = client.get("/users")
    assert rv.status_code == 200
    users = rv.get_json()
    assert any(u["id"] == reviewer_id for u in users)

    # request review
    rv = client.post(f"/request-review/{file_id}", json={"reviewer_id": reviewer_id})
    assert rv.status_code == 201
    review_id = rv.get_json()["modified_version"]

    # cancel review request
    rv = client.post(f"/cancel-review/{file_id}")
    assert rv.status_code == 200
    assert rv.get_json()["message"] == "Review request cancelled successfully"

    # re-request review
    rv = client.post(f"/request-review/{file_id}", json={"reviewer_id": reviewer_id})
    assert rv.status_code == 201

    # logout requester → reviewer login
    client.post("/logout")
    client.post("/login", json={"username":"rev", "password":"pwd"})

    # reviewer list assigned reviews
    rv = client.get("/my-reviews")
    reviews = rv.get_json()
    assert len(reviews) > 0
    rid = reviews[-1]["id"]

    # check notifications
    rv = client.get("/notifications")
    notes = rv.get_json()
    assert len(notes) > 0

    # read notification
    rv = client.post(f"/notifications/{notes[0]['id']}/read")
    assert rv.status_code == 200
    assert rv.get_json()["message"] == "Notification marked as read"

    # read all notifications
    rv = client.post("/notifications/mark-all-read")
    assert rv.status_code == 200
    assert rv.get_json()["message"] == "All notifications marked as read"

    # approve
    rv = client.post(f"/review/{rid}", json={"decision":"approved", "comments":"LGTM"})
    assert rv.status_code == 200

    # get published file
    rv = client.get(f"/public-files")
    published_files = rv.get_json()
    assert len(published_files) > 0

    # review comparison
    rv = client.get(f"/review-comparison/{rid}")
    assert rv.status_code == 200

    # requester gets notification
    client.post("/logout")
    client.post("/login", json={"username":"req", "password":"pwd"})
    rv = client.get("/notifications")
    notes = rv.get_json()
    assert any("approved" in n["title"].lower() for n in notes)
