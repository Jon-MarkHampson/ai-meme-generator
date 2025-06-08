import pytest


@pytest.fixture
def make_request(auth_client):
    resp = auth_client.post(
        "/caption_requests/",
        json={"prompt_text": "Cascade test", "request_method": "DIRECT"},
    )
    return resp.json()["id"]


@pytest.fixture
def variant_payload(make_request):
    return {
        "request_id": make_request,
        "variant_rank": 1,
        "caption_text": ["Line 1", "Line 2"],
        "model_name": "test-model",
    }


def test_create_and_read_variant(auth_client, variant_payload):
    # Create
    post = auth_client.post("/caption_variants/", json=variant_payload)
    assert post.status_code == 201
    v = post.json()
    assert v["variant_rank"] == variant_payload["variant_rank"]
    assert v["caption_text"] == variant_payload["caption_text"]
    vid = v["id"]

    # Read
    get = auth_client.get(f"/caption_variants/{vid}")
    assert get.status_code == 200
    assert get.json()["id"] == vid


def test_list_variants(auth_client, variant_payload):
    auth_client.post("/caption_variants/", json=variant_payload)
    lst = auth_client.get("/caption_variants/")
    assert lst.status_code == 200
    data = lst.json()
    assert "variants" in data
    assert isinstance(data["variants"], list)
    assert len(data["variants"]) >= 1


def test_patch_variant(auth_client, variant_payload):
    post = auth_client.post("/caption_variants/", json=variant_payload)
    vid = post.json()["id"]
    # update rank
    patch = auth_client.patch(f"/caption_variants/{vid}", json={"variant_rank": 5})
    assert patch.status_code == 200
    assert patch.json()["variant_rank"] == 5


def test_delete_variant(auth_client, variant_payload):
    post = auth_client.post("/caption_variants/", json=variant_payload)
    vid = post.json()["id"]
    delete = auth_client.delete(f"/caption_variants/{vid}")
    assert delete.status_code == 204

    # confirm 404
    missing = auth_client.get(f"/caption_variants/{vid}")
    assert missing.status_code == 404


def test_cascade_delete_request_removes_variants(auth_client, make_request, session):
    # create two variants
    payload = {
        "request_id": make_request,
        "variant_rank": 1,
        "caption_text": ["A"],
        "model_name": "m",
    }
    for _ in range(2):
        auth_client.post("/caption_variants/", json=payload)

    # should see them
    assert len(auth_client.get("/caption_variants/").json()["variants"]) == 2

    # delete the parent request
    auth_client.delete(f"/caption_requests/{make_request}")

    # now no variants
    out = auth_client.get("/caption_variants/")
    assert out.status_code == 200
    assert out.json()["variants"] == []
