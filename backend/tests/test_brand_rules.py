from conftest import AS_OF, observation


def test_saved_category_controls_feed_and_empty_category_restores_all_niches(client, settings):
    from pulso.admin import load_observations

    load_observations(
        settings, [observation(), observation("9000000000000000002", category="Fitness")], as_of=AS_OF
    )
    initial = client.get("/v1/brand-rules")
    assert initial.status_code == 200
    assert initial.json()["version"] == 0
    saved = client.patch("/v1/brand-rules", json={"expected_version": 0, "category_text": "  Culinária  "})
    assert saved.status_code == 200
    assert saved.json()["category_text"] == "Culinária"
    feed = client.get("/v1/top-videos").json()
    assert feed["category"] == "Culinária"
    assert [v["id"] for v in feed["items"]] == ["9000000000000000001"]
    assert client.patch("/v1/brand-rules", json={"expected_version": 0, "tone": "Leve"}).status_code == 409
    cleared = client.patch("/v1/brand-rules", json={"expected_version": 1, "category_text": "   "})
    assert cleared.json()["category_text"] is None
    assert client.get("/v1/top-videos").json()["eligible_count"] == 2


def test_unknown_free_text_category_remains_visible_without_results(client):
    saved = client.patch("/v1/brand-rules", json={"expected_version": 0, "category_text": "Cerâmica autoral"})
    assert saved.json()["category_text"] == "Cerâmica autoral"
    feed = client.get("/v1/top-videos").json()
    assert feed["category"] == "Cerâmica autoral"
    assert feed["items"] == []
