def test_creator_requires_preview_confirmation_and_can_be_restored(client):
    from pulso.jobs import drain_once

    class Profiles:
        def profile(self, handle):
            return {"id": "canonical-123", "handle": "cozinha", "name": "Cozinha de teste", "available": True}

        def collect(self, source, reference, count):
            return []

    client.app.state.collector = Profiles()
    added = client.post("/v1/creators", json={"input": "@cozinha"})
    assert added.status_code == 202
    ref = added.json()["id"]
    drain_once(client.app)
    preview = client.get("/v1/creators").json()["items"][0]
    assert preview["status"] == "preview"
    assert preview["creator_id"] == "canonical-123"
    assert client.post(f"/v1/creators/{ref}/confirm", json={"creator_id": "wrong"}).status_code == 409
    assert (
        client.post(f"/v1/creators/{ref}/confirm", json={"creator_id": "canonical-123"}).json()["status"]
        == "active"
    )
    assert client.delete(f"/v1/creators/{ref}").status_code == 200
    assert client.get("/v1/creators").json()["items"] == []
    assert client.post(f"/v1/creators/{ref}/restore").json()["status"] == "active"


def test_creator_reference_cannot_be_seen_from_another_workspace(client, settings):
    from pulso.admin import provision

    created = client.post("/v1/creators", json={"input": "@cozinha"}).json()
    provision(settings, "other@example.test", "another-secure-password", "Outro workspace")
    login = client.post(
        "/v1/auth/login", json={"email": "other@example.test", "password": "another-secure-password"}
    )
    client.headers["x-csrf-token"] = login.json()["csrf_token"]
    assert client.get("/v1/creators").json()["items"] == []
    assert client.delete(f"/v1/creators/{created['id']}").status_code == 404
