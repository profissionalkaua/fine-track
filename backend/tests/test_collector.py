import pytest


def test_tiktok_bootstrap_cdn_allows_public_addresses_and_rejects_private_dns(monkeypatch):
    import socket

    from pulso.adapters.tiktok import safe_public_url

    url = "https://sf16-website-login.neutral.ttwstatic.com/obj/test/bootstrap.js"
    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **kw: [(2, 1, 6, "", ("8.8.8.8", 443))])
    assert safe_public_url(url) == url
    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **kw: [(2, 1, 6, "", ("127.0.0.1", 443))])
    with pytest.raises(ValueError, match="interno"):
        safe_public_url(url)


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


def test_profile_resolution_stops_after_global_source_block(client, settings):
    from pulso.adapters.tiktok import SourceError
    from pulso.jobs import drain_once

    class Blocked:
        def collect(self, source, reference, count):
            raise SourceError("Acesso bloqueado pela fonte.", "blocked")

        def profile(self, handle):
            raise AssertionError("A fonte suspensa não pode receber novas consultas de perfil.")

    client.app.state.collector = Blocked()
    settings.collection_enabled = True
    client.get("/v1/top-videos")
    drain_once(client.app)
    profile = client.post("/v1/creators", json={"input": "@nao.consultar"}).json()
    drain_once(client.app)
    saved = next(item for item in client.get("/v1/creators").json()["items"] if item["id"] == profile["id"])
    assert saved["status"] == "unavailable"
    assert "suspensa" in saved["error"].lower()
