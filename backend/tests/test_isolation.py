def test_viewer_cannot_modify_brand_references_or_create_runs(client, settings):
    from pulso.admin import provision

    workspace_id = client.get("/v1/auth/me").json()["workspace"]["id"]
    provision(
        settings,
        "viewer@example.test",
        "secure-viewer-password",
        "",
        role="viewer",
        workspace_id=workspace_id,
    )
    login = client.post(
        "/v1/auth/login", json={"email": "viewer@example.test", "password": "secure-viewer-password"}
    )
    client.headers["x-csrf-token"] = login.json()["csrf_token"]
    assert client.get("/v1/brand-rules").status_code == 200
    assert client.patch("/v1/brand-rules", json={"expected_version": 0, "tone": "Outro"}).status_code == 403
    assert client.post("/v1/creators", json={"input": "@teste"}).status_code == 403
    assert (
        client.post(
            "/v1/runs", json={"scope": "feed"}, headers={"Idempotency-Key": "viewer-denied-01"}
        ).status_code
        == 403
    )


def test_private_rules_and_run_exports_are_isolated_by_workspace(client, settings):
    from pulso.admin import provision

    client.patch("/v1/brand-rules", json={"expected_version": 0, "tone": "Segredo da marca A"})
    run_id = client.post(
        "/v1/runs", json={"scope": "feed"}, headers={"Idempotency-Key": "private-run-001"}
    ).json()["id"]
    provision(settings, "workspace-b@example.test", "secure-workspace-b-password", "Marca B")
    login = client.post(
        "/v1/auth/login",
        json={"email": "workspace-b@example.test", "password": "secure-workspace-b-password"},
    )
    client.headers["x-csrf-token"] = login.json()["csrf_token"]
    assert client.get("/v1/brand-rules").json()["version"] == 0
    assert client.get("/v1/runs").json()["items"] == []
    assert client.get(f"/v1/runs/{run_id}/export").status_code == 404


def test_cross_origin_mutation_is_rejected_even_with_valid_csrf(client):
    assert (
        client.patch(
            "/v1/preferences", json={"country": "PT"}, headers={"Origin": "https://evil.test"}
        ).status_code
        == 403
    )
