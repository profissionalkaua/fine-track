from conftest import AS_OF, observation


def test_feed_orders_by_measured_velocity_and_preserves_unknown_metrics(client, settings):
    from pulso.admin import load_observations

    load_observations(
        settings,
        [
            observation("9000000000000000001", end_views=23000),
            observation("9000000000000000002", end_views=45000),
        ],
        as_of=AS_OF,
    )
    body = client.get("/v1/top-videos").json()
    assert [v["id"] for v in body["items"]] == ["9000000000000000002", "9000000000000000001"]
    assert body["items"][0]["velocity"] == 2000
    assert body["items"][0]["delta_views"] == 44000
    assert body["items"][0]["likes"] is None
    assert body["eligible_count"] == 2
    assert body["coverage_status"] == "partial_coverage"


def test_feed_rejects_unknown_country_and_recovers_invalid_cursor(client):
    assert client.get("/v1/top-videos?country=ZZ").status_code == 422
    assert client.get("/v1/top-videos?cursor=invalid").status_code == 409


def test_missing_pairs_are_separate_from_growth_ranking(client, settings):
    from pulso.admin import load_observations

    item = observation()
    item["snapshots"] = item["snapshots"][-1:]
    load_observations(settings, [item], as_of=AS_OF)
    data = client.get("/v1/top-videos").json()
    assert data["items"] == []
    assert data["eligible_count"] == 0
    assert data["most_viewed"][0]["views"] == 45000


def test_cursor_pins_version_and_never_repeats_entries(client, settings):
    from pulso.admin import load_observations

    load_observations(
        settings,
        [observation(str(9000000000000000000 + i), end_views=1000 + 22000 * i) for i in range(1, 4)],
        as_of=AS_OF,
    )
    page1 = client.get("/v1/top-videos?limit=2").json()
    page2 = client.get("/v1/top-videos", params={"limit": 2, "cursor": page1["cursor"]}).json()
    assert [v["rank"] for v in page1["items"]] == [1, 2]
    assert [v["rank"] for v in page2["items"]] == [3]
    assert page2["version"] == page1["version"]
    assert (
        client.get("/v1/top-videos", params={"country": "PT", "cursor": page1["cursor"]}).status_code == 409
    )


def test_country_preference_is_saved_for_next_visit(client):
    result = client.patch("/v1/preferences", json={"country": "PT"})
    assert result.status_code == 200
    assert client.get("/v1/top-videos").json()["country"] == "PT"


def test_mutations_require_csrf(client):
    client.headers.pop("x-csrf-token")
    assert client.post("/v1/auth/logout").status_code == 403
