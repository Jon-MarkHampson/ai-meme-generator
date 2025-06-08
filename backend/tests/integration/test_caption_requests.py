import pytest


@pytest.fixture
def cr_payload():
    return {"prompt_text": "Make a meme", "request_method": "DIRECT"}


def test_create_and_read_caption_request(auth_client, cr_payload):
    # Create
    post = auth_client.post("/caption_requests/", json=cr_payload)
    assert post.status_code == 201
    cr = post.json()
    assert cr["prompt_text"] == cr_payload["prompt_text"]
    rid = cr["id"]

    # Read back
    get = auth_client.get(f"/caption_requests/{rid}")
    assert get.status_code == 200
    assert get.json()["id"] == rid


def test_list_caption_requests(auth_client, cr_payload):
    # ensure at least one exists
    auth_client.post("/caption_requests/", json=cr_payload)
    lst = auth_client.get("/caption_requests/")
    assert lst.status_code == 200
    data = lst.json()
    assert "requests" in data
    assert isinstance(data["requests"], list)
    assert len(data["requests"]) >= 1


def test_patch_caption_request_noop(auth_client, cr_payload):
    post = auth_client.post("/caption_requests/", json=cr_payload)
    rid = post.json()["id"]
    patch = auth_client.patch(f"/caption_requests/{rid}", json={})
    assert patch.status_code == 200
    assert patch.json()["id"] == rid


def test_delete_caption_request(auth_client, cr_payload):
    post = auth_client.post("/caption_requests/", json=cr_payload)
    rid = post.json()["id"]
    delete = auth_client.delete(f"/caption_requests/{rid}")
    assert delete.status_code == 204

    # confirm 404 afterwards
    missing = auth_client.get(f"/caption_requests/{rid}")
    assert missing.status_code == 404
