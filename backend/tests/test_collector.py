import pytest


def test_normalization_keeps_large_ids_null_metrics_and_uncertain_country():
    from pulso.adapters.tiktok import normalize_video

    item = normalize_video(
        {
            "id": "9000000000000000001",
            "desc": "Receita #Receitas",
            "createTime": 1795000000,
            "author": {"id": "123", "uniqueId": "cozinha"},
            "stats": {"playCount": 1000},
            "challenges": [{"title": "Receitas"}, {"title": "receitas"}],
            "video": {},
        }
    )
    assert item["id"] == "9000000000000000001"
    assert item["country"] is None
    assert item["snapshots"][0]["likes"] is None
    assert item["hashtags"] == ["Receitas"]


@pytest.mark.parametrize(
    "value",
    [
        "http://127.0.0.1/admin",
        "https://tiktok.com.evil.test/@x",
        "https://www.tiktok.com@localhost/@x",
        "https://www.tiktok.com:8080/@x",
    ],
)
def test_creator_url_validation_rejects_other_destinations(value):
    from pulso.adapters.tiktok import parse_handle

    with pytest.raises(ValueError):
        parse_handle(value)


def test_background_collection_publishes_feed_without_duplicate_jobs(client, settings):
    from conftest import observation

    from pulso.jobs import drain_once

    class FixtureCollector:
        def collect(self, source, reference, count):
            return [observation()]

    client.app.state.collector = FixtureCollector()
    settings.collection_enabled = True
    first = client.get("/v1/top-videos").json()
    assert first["coverage_status"] == "collecting"
    assert client.get("/v1/top-videos").json()["collection_id"] == first["collection_id"]
    drain_once(client.app)
    result = client.get("/v1/top-videos").json()
    assert result["eligible_count"] == 1
    assert result["items"][0]["id"] == "9000000000000000001"
