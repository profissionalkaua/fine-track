def test_workspace_switch_requires_membership_and_changes_rule_visibility(client, settings):
    from pulso.admin import provision

    client.patch("/v1/brand-rules", json={"expected_version": 0, "tone": "Workspace A"})
    other = provision(settings, "owner@example.test", "a-secure-test-password", "Workspace B")
    options = client.get("/v1/workspaces")
    assert options.status_code == 200
    assert len(options.json()["items"]) == 2
    assert client.post("/v1/auth/workspace", json={"workspace_id": "unknown"}).status_code == 403
    changed = client.post("/v1/auth/workspace", json={"workspace_id": other["workspace_id"]})
    assert changed.status_code == 200
    client.headers["x-csrf-token"] = changed.json()["csrf_token"]
    assert changed.json()["workspace"]["name"] == "Workspace B"
    assert client.get("/v1/brand-rules").json()["version"] == 0


def test_repeated_owner_provision_does_not_duplicate_the_same_workspace(client, settings):
    from pulso.admin import provision

    provision(settings, "owner@example.test", "a-secure-test-password", "Estúdio de teste")
    assert len(client.get("/v1/workspaces").json()["items"]) == 1


def test_stale_workspace_request_cannot_write_to_new_session_workspace(client, settings):
    from pulso.admin import provision

    original = client.get("/v1/auth/me").json()["workspace"]["id"]
    target = provision(settings, "owner@example.test", "a-secure-test-password", "Workspace B")[
        "workspace_id"
    ]
    changed = client.post("/v1/auth/workspace", json={"workspace_id": target}).json()
    client.headers["x-csrf-token"] = changed["csrf_token"]
    result = client.patch(
        "/v1/brand-rules",
        json={"expected_version": 0, "tone": "Texto do workspace anterior"},
        headers={"X-Workspace-ID": original},
    )
    assert result.status_code == 409
    assert client.get("/v1/brand-rules").json()["version"] == 0
