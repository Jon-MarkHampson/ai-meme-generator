import pytest


def test_login_success(client, test_user):
    # correct credentials
    resp = client.post(
        "/auth/login",
        json={"email": test_user.email, "password": "password123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_failure_bad_password(client, test_user):
    resp = client.post(
        "/auth/login",
        json={"email": test_user.email, "password": "wrong"},
    )
    assert resp.status_code == 401


def test_login_failure_unknown_user(client):
    resp = client.post(
        "/auth/login",
        json={"email": "noone@example.com", "password": "whatever"},
    )
    assert resp.status_code == 401
