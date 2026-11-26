from conftest import AS_OF, observation


def test_individual_lookup_recovers_active_run_beyond_recent_history(client, settings):
    from datetime import timedelta

    from pulso.admin import load_observations

    load_observations(settings, [observation()], as_of=AS_OF)
    video_id = "9000000000000000001"
    created = client.post(
        "/v1/runs",
        json={"scope": "video", "video_id": video_id},
        headers={"Idempotency-Key": "recover-individual"},
    ).json()
    client.app.state.clock = lambda: AS_OF + timedelta(minutes=1)
    for i in range(21):
        assert (
            client.post(
                "/v1/runs",
                json={"scope": "feed"},
                headers={"Idempotency-Key": f"later-feed-run-{i}"},
            ).status_code
            == 202
        )
    recent = client.get("/v1/runs").json()["items"]
    assert created["id"] not in {run["id"] for run in recent}
    response = client.get(f"/v1/runs/available?video_id={video_id}&rules_version=0")
    assert response.status_code == 200
    assert response.json()["run"]["id"] == created["id"]
    assert response.json()["run"]["state"] == "queued"
    assert client.get("/v1/runs").json()["items"] == recent


def test_individual_lookup_reuses_completed_result_until_rules_or_model_change(client, settings):
    from pulso.admin import load_observations
    from pulso.jobs import drain_once

    class Generator:
        model_version = "test-only"

        def generate(self, references, rules, count):
            return generated(count)

    client.app.state.generator = Generator()
    load_observations(settings, [observation()], as_of=AS_OF)
    body = {"scope": "video", "video_id": "9000000000000000001"}
    created = client.post("/v1/runs", json=body, headers={"Idempotency-Key": "completed-lookup"}).json()
    drain_once(client.app)
    url = "/v1/runs/available?video_id=9000000000000000001"
    assert client.get(url).json()["run"]["state"] == "completed"
    assert client.get(url).json()["run"]["id"] == created["id"]
    settings.ollama_model = "another-model"
    assert client.get(url).json()["run"] is None
    settings.ollama_model = ""
    client.patch("/v1/brand-rules", json={"expected_version": 0, "category_text": "Fitness"})
    assert client.get(url).json()["run"] is None
    assert client.get(url + "&rules_version=0").status_code == 409


def test_opening_same_individual_reuses_job_but_explicit_retry_creates_one(client, settings):
    from concurrent.futures import ThreadPoolExecutor

    from pulso.admin import load_observations, provision

    load_observations(settings, [observation()], as_of=AS_OF)
    body = {"scope": "video", "video_id": "9000000000000000001"}
    first = client.post("/v1/runs/video/open", json=body, headers={"Idempotency-Key": "open-first-001"})
    assert first.status_code == 202
    second = client.post("/v1/runs/video/open", json=body, headers={"Idempotency-Key": "open-again-001"})
    assert second.json()["id"] == first.json()["id"]
    assert len(client.get("/v1/runs").json()["items"]) == 1
    other = {"scope": "video", "video_id": "9000000000000000002"}
    load_observations(settings, [observation(other["video_id"])], as_of=AS_OF)

    def open_video(key):
        return client.post("/v1/runs/video/open", json=other, headers={"Idempotency-Key": key})

    with ThreadPoolExecutor(max_workers=2) as pool:
        simultaneous = list(pool.map(open_video, ["simultaneous-001", "simultaneous-002"]))
    assert all(response.status_code == 202 for response in simultaneous)
    assert simultaneous[0].json()["id"] == simultaneous[1].json()["id"]
    assert (
        client.post("/v1/runs", json=body, headers={"Idempotency-Key": "explicit-retry-001"}).json()["id"]
        != first.json()["id"]
    )
    provision(settings, "another@example.test", "secure-another-password", "Another workspace")
    login = client.post(
        "/v1/auth/login", json={"email": "another@example.test", "password": "secure-another-password"}
    )
    client.headers["x-csrf-token"] = login.json()["csrf_token"]
    assert client.get("/v1/runs/available?video_id=9000000000000000001").json()["run"] is None


def test_individual_lookup_invalidates_changed_reference_and_supports_viewer(client, settings):
    from pulso.admin import load_observations, provision

    load_observations(settings, [observation()], as_of=AS_OF)
    body = {"scope": "video", "video_id": "9000000000000000001"}
    created = client.post("/v1/runs", json=body, headers={"Idempotency-Key": "viewer-reuse-001"}).json()
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
    url = "/v1/runs/available?video_id=9000000000000000001"
    assert client.get(url).json()["run"]["id"] == created["id"]
    assert (
        client.post(
            "/v1/runs/video/open", json=body, headers={"Idempotency-Key": "viewer-open-denied"}
        ).status_code
        == 403
    )
    updated = observation()
    updated["description"] = "Uma nova descrição da referência"
    load_observations(settings, [updated], as_of=AS_OF)
    assert client.get(url).json()["run"] is None


def test_run_freezes_inputs_and_reuses_idempotency_key(client, settings):
    from pulso.admin import load_observations

    load_observations(settings, [observation(str(9000000000000000000 + i)) for i in range(1, 6)], as_of=AS_OF)
    headers = {"Idempotency-Key": "stable-test-request"}
    body = {"scope": "feed", "country": "BR", "period": "day"}
    created = client.post("/v1/runs", json=body, headers=headers)
    assert created.status_code == 202
    run_id = created.json()["id"]
    assert client.post("/v1/runs", json=body, headers=headers).json()["id"] == run_id
    assert client.post("/v1/runs", json={**body, "country": "PT"}, headers=headers).status_code == 409
    saved = client.get(f"/v1/runs/{run_id}").json()
    assert saved["frozen"]["country"] == "BR"
    assert saved["frozen"]["rules_version"] == 0
    assert len(saved["frozen"]["references"]) == 5
    client.patch("/v1/brand-rules", json={"expected_version": 0, "category_text": "Fitness"})
    assert client.get(f"/v1/runs/{run_id}").json()["frozen"]["category"] is None


def generated(count, reference_id="9000000000000000001"):
    return {
        "ideas": [
            {
                "title": f"Uma ideia original {i + 1}",
                "premise": "Uma receita explicada por escolhas.",
                "justification": "A descrição da referência aborda receitas práticas.",
                "reference_ids": [reference_id],
                "intent": "Ensinar uma técnica com voz própria.",
                "hook": "Uma escolha muda o resultado da sua receita.",
                "script": [
                    {"label": "Abertura", "text": "Mostre duas formas de preparar o mesmo ingrediente."},
                    {"label": "Desenvolvimento", "text": "Explique uma diferença e demonstre o resultado."},
                ],
                "on_screen_text": "Teste uma escolha por vez",
                "cta": "Qual versão você experimentaria?",
                "estimated_duration_seconds": 30,
                "basis": "editorial_hypothesis",
            }
            for i in range(count)
        ]
    }


def test_general_run_generates_five_ideas_with_existing_references(client, settings):
    from pulso.admin import load_observations
    from pulso.jobs import drain_once

    class Generator:
        model_version = "test-only"

        def generate(self, references, rules, count):
            return generated(count)

    client.app.state.generator = Generator()
    load_observations(settings, [observation(str(9000000000000000000 + i)) for i in range(1, 6)], as_of=AS_OF)
    run_id = client.post(
        "/v1/runs", json={"scope": "feed"}, headers={"Idempotency-Key": "five-ideas-test"}
    ).json()["id"]
    drain_once(client.app)
    result = client.get(f"/v1/runs/{run_id}").json()
    assert result["state"] == "completed"
    assert len(result["result"]["ideas"]) == 5
    assert result["processed"] == 5
    assert result["result"]["evidence"][0]["video_id"] == "9000000000000000001"
    exported = client.get(f"/v1/runs/{run_id}/export").json()
    assert exported["schema_version"] == "1.0"
    assert exported["result"]["model_version"] == "test-only"


def test_cancellation_prevents_late_generation_from_publishing(client, settings):
    from pulso.admin import load_observations
    from pulso.jobs import drain_once

    load_observations(settings, [observation(str(9000000000000000000 + i)) for i in range(1, 6)], as_of=AS_OF)
    run_id = client.post(
        "/v1/runs", json={"scope": "feed"}, headers={"Idempotency-Key": "cancel-test-001"}
    ).json()["id"]

    class Generator:
        model_version = "test-only"

        def generate(self, references, rules, count):
            assert client.post(f"/v1/runs/{run_id}/cancel").status_code == 200
            return generated(count)

    client.app.state.generator = Generator()
    drain_once(client.app)
    result = client.get(f"/v1/runs/{run_id}").json()
    assert result["state"] == "cancelled"
    assert result["result"] is None


def test_insufficient_references_are_partial_and_can_resume(client):
    from pulso.jobs import drain_once

    run_id = client.post(
        "/v1/runs", json={"scope": "feed"}, headers={"Idempotency-Key": "partial-test-001"}
    ).json()["id"]
    drain_once(client.app)
    result = client.get(f"/v1/runs/{run_id}").json()
    assert result["state"] == "partial"
    assert result["errors"][0]["code"] == "insufficient_references"
    assert result["result"]["unavailable_signals"] == ["retention_analytics", "audio", "visual_frames"]
    assert result["result"]["signal_availability"] == {}
    resumed = client.post(f"/v1/runs/{run_id}/resume", headers={"Idempotency-Key": "resume-test-0001"})
    assert resumed.status_code == 202
    assert resumed.json()["id"] != run_id
    assert resumed.json()["parent_id"] == run_id


def test_individual_run_accepts_one_video_and_exports_visual_absence(client, settings):
    from pulso.admin import load_observations
    from pulso.jobs import drain_once

    class Generator:
        model_version = "test-only"

        def generate(self, references, rules, count):
            return generated(count)

    client.app.state.generator = Generator()
    load_observations(settings, [observation()], as_of=AS_OF)
    created = client.post(
        "/v1/runs",
        json={"scope": "video", "video_id": "9000000000000000001", "rules_version": 0},
        headers={"Idempotency-Key": "individual-0001"},
    )
    assert created.status_code == 202
    drain_once(client.app)
    exported = client.get(f"/v1/runs/{created.json()['id']}/export").json()
    assert len(exported["result"]["ideas"]) == 1
    assert exported["result"]["analise_visual"]["state"] == "unavailable"
    assert exported["frozen"]["references"][0]["id"] == "9000000000000000001"


def test_model_cannot_publish_invented_reference_ids(client, settings):
    from pulso.admin import load_observations
    from pulso.jobs import drain_once

    class Generator:
        model_version = "test-only"

        def generate(self, references, rules, count):
            return generated(count, "fabricated-reference")

    client.app.state.generator = Generator()
    load_observations(settings, [observation()], as_of=AS_OF)
    run_id = client.post(
        "/v1/runs",
        json={"scope": "video", "video_id": "9000000000000000001"},
        headers={"Idempotency-Key": "hostile-model-01"},
    ).json()["id"]
    drain_once(client.app)
    result = client.get(f"/v1/runs/{run_id}").json()
    assert result["state"] == "failed"
    assert result["result"] is None


def test_preview_shows_eligible_references_without_creating_run(client, settings):
    from pulso.admin import load_observations

    load_observations(settings, [observation()], as_of=AS_OF)
    preview = client.post("/v1/runs/preview", json={"scope": "feed"})
    assert preview.status_code == 200
    assert preview.json()["eligible_count"] == 1
    assert client.get("/v1/runs").json()["items"] == []


def test_unexpected_provider_failure_does_not_leave_run_stuck_in_progress(client, settings):
    from pulso.admin import load_observations
    from pulso.jobs import drain_once

    class Generator:
        model_version = "test-only"

        def generate(self, references, rules, count):
            raise RuntimeError("simulated external process failure")

    client.app.state.generator = Generator()
    load_observations(settings, [observation()], as_of=AS_OF)
    run_id = client.post(
        "/v1/runs",
        json={"scope": "video", "video_id": "9000000000000000001"},
        headers={"Idempotency-Key": "process-failure-001"},
    ).json()["id"]
    drain_once(client.app)
    result = client.get(f"/v1/runs/{run_id}").json()
    assert result["state"] == "failed"
    assert result["errors"][0]["code"] == "worker_failed"


def test_run_accepts_loaded_references_beyond_the_first_fifty_positions(client, settings):
    from pulso.admin import load_observations

    records = [
        observation(
            str(9000000000000000000 + i),
            end_views=1000 + 22000 * (61 - i),
            tags=["later"] if i == 55 else ["other"],
        )
        for i in range(1, 61)
    ]
    load_observations(settings, records, as_of=AS_OF)
    first = client.get("/v1/top-videos").json()
    second = client.get("/v1/top-videos", params={"cursor": first["cursor"]}).json()
    third = client.get("/v1/top-videos", params={"cursor": second["cursor"]}).json()
    selected = next(item for item in third["items"] if item["hashtags"][0]["key"] == "later")
    created = client.post(
        "/v1/runs",
        json={
            "scope": "feed",
            "ranking_version": first["version"],
            "video_ids": [selected["id"]],
            "hashtag": "later",
        },
        headers={"Idempotency-Key": "third-page-run-01"},
    )
    assert created.status_code == 202
    assert created.json()["frozen"]["references"][0]["id"] == selected["id"]
