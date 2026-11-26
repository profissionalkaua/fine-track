import subprocess

import imageio_ffmpeg
import pytest
from conftest import AS_OF, observation


@pytest.mark.parametrize("model_fails", [True, False])
def test_media_result_keeps_signal_availability_when_text_generation_finishes(
    client, settings, tmp_path, model_fails
):
    from pulso.adapters.ollama import ModelError
    from pulso.admin import load_observations, register_media
    from pulso.jobs import drain_once

    settings.media_root = str(tmp_path)
    settings.media_temp_root = str(tmp_path / "work")
    path = tmp_path / "authorized.mp4"
    subprocess.run(
        [
            imageio_ffmpeg.get_ffmpeg_exe(),
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=c=blue:s=160x120:d=2",
            "-y",
            str(path),
        ],
        check=True,
        timeout=30,
    )
    load_observations(settings, [observation()], as_of=AS_OF)
    workspace_id = client.get("/v1/auth/me").json()["workspace"]["id"]
    register_media(settings, workspace_id, "9000000000000000001", path, "synthetic-owned")

    class Generator:
        model_version = "test-only"

        def generate(self, references, rules, count):
            from test_runs import generated

            if model_fails:
                raise ModelError("Modelo de texto temporariamente indisponível.")
            return generated(count)

    client.app.state.generator = Generator()
    run_id = client.post(
        "/v1/runs",
        json={"scope": "video", "video_id": "9000000000000000001"},
        headers={"Idempotency-Key": "visual-preserved-001"},
    ).json()["id"]
    drain_once(client.app)
    exported = client.get(f"/v1/runs/{run_id}/export").json()
    assert exported["state"] == ("failed" if model_fails else "completed")
    assert exported["result"]["analise_visual"]["duration_ms"] == 2000
    assert exported["result"]["analise_visual"]["frames"][0]["timestamp_ms"] == 0
    assert exported["result"]["unavailable_signals"] == ["retention_analytics", "audio"]
    assert exported["result"]["signal_availability"]["9000000000000000001"] == {
        "retention_analytics": False, "audio": False, "visual_frames": True
    }


def test_scheduler_observes_creators_beyond_the_first_six(client, settings):
    from pulso.jobs import drain_once
    from pulso.scheduler import schedule_once

    class Profiles:
        def profile(self, handle):
            return {"id": handle, "handle": handle, "name": handle, "available": True}

        def collect(self, source, reference, count):
            if source != "creator":
                return []
            index = int(reference.split("_")[-1])
            item = observation(str(9000000000000000000 + index), country=None)
            item["creator_id"] = reference
            item["handle"] = reference
            return [item]

    client.app.state.collector = Profiles()
    saved = []
    for index in range(1, 8):
        saved.append(client.post("/v1/creators", json={"input": f"@creator_{index}"}).json())
    drain_once(client.app)
    for ref in saved:
        preview = next(p for p in client.get("/v1/creators").json()["items"] if p["id"] == ref["id"])
        client.post(f"/v1/creators/{ref['id']}/confirm", json={"creator_id": preview["creator_id"]})
    settings.collection_enabled = True
    schedule_once(client.app)
    drain_once(client.app)
    last = client.get(f"/v1/creators/{saved[-1]['id']}/videos").json()
    assert [v["id"] for v in last["items"]] == ["9000000000000000007"]
