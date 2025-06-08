def test_read_current_user(auth_client, test_user):
    resp = auth_client.get("/users/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == test_user.email
    assert data["first_name"] == test_user.first_name


def test_update_current_user(auth_client):
    # change first and last name
    resp = auth_client.patch(
        "/users/me",
        json={
            "current_password": "password123",
            "first_name": "NewFirst",
            "last_name": "NewLast",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["first_name"] == "NewFirst"
    assert data["last_name"] == "NewLast"

    # verify persisted
    again = auth_client.get("/users/me")
    assert again.json()["first_name"] == "NewFirst"


def test_delete_current_user(auth_client):
    # deleting with correct password returns 204
    resp = auth_client.delete("/users/me", json={"password": "password123"})
    assert resp.status_code == 204

    # now token no longer works
    fail = auth_client.get("/users/me")
    assert fail.status_code == 401
