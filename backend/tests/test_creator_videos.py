from conftest import AS_OF, observation


def test_saved_creator_recent_videos_do_not_require_country_evidence(client, settings):
    from pulso.admin import load_observations
    from pulso.jobs import drain_once

    class Profiles:
        def profile(self, handle):
            return {"id": "creator-1", "handle": "cozinha", "name": "Cozinha", "available": True}

    client.app.state.collector = Profiles()
    ref = client.post("/v1/creators", json={"input": "@cozinha"}).json()["id"]
    drain_once(client.app)
    client.post(f"/v1/creators/{ref}/confirm", json={"creator_id": "creator-1"})
    load_observations(settings, [observation(country=None)], as_of=AS_OF)
    result = client.get(f"/v1/creators/{ref}/videos").json()
    assert [v["id"] for v in result["items"]] == ["9000000000000000001"]
