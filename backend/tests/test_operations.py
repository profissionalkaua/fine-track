def test_operational_metrics_count_api_requests_without_tenant_labels(client):
    client.get("/v1/top-videos")
    result = client.get("/metrics")
    assert result.status_code == 200
    assert "pulso_http_requests_total" in result.text
    assert "/v1/top-videos" in result.text
    assert "owner@example.test" not in result.text


def test_login_is_rate_limited_after_repeated_invalid_attempts(client):
    for _ in range(10):
        client.post("/v1/auth/login", json={"email": "attack@example.test", "password": "wrong"})
    assert (
        client.post("/v1/auth/login", json={"email": "attack@example.test", "password": "wrong"}).status_code
        == 429
    )
