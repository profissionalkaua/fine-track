import subprocess

import imageio_ffmpeg
from conftest import AS_OF, observation
from test_runs import generated


def test_individual_run_uses_authorized_media_and_keeps_script_when_vision_is_missing(
    client, settings, tmp_path
):
    from pulso.admin import load_observations, register_media
    from pulso.jobs import drain_once

    settings.media_root = str(tmp_path)
    settings.media_temp_root = str(tmp_path / "work")
    video = tmp_path / "authorized.mp4"
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
            str(video),
        ],
        check=True,
        timeout=30,
    )
    load_observations(settings, [observation()], as_of=AS_OF)
    workspace_id = client.get("/v1/auth/me").json()["workspace"]["id"]
    register_media(settings, workspace_id, "9000000000000000001", video, "synthetic-test-owned")

    class Generator:
        model_version = "test-only"

        def generate(self, references, rules, count):
            return generated(count)

    client.app.state.generator = Generator()
    run_id = client.post(
        "/v1/runs",
        json={"scope": "video", "video_id": "9000000000000000001"},
        headers={"Idempotency-Key": "authorized-media-001"},
    ).json()["id"]
    drain_once(client.app)
    result = client.get(f"/v1/runs/{run_id}").json()
    assert len(result["result"]["ideas"]) == 1
    assert result["result"]["analise_visual"]["duration_ms"] == 2000
    assert result["result"]["analise_visual"]["state"] == "partial"
    assert result["result"]["analise_visual"]["frames"][0]["timestamp_ms"] == 0
    lookup = "/v1/runs/available?video_id=9000000000000000001"
    assert client.get(lookup).json()["run"]["id"] == run_id
    # A renewed authorization for changed bytes must not reuse the previous result.
    video.write_bytes(video.read_bytes() + b"\0")
    register_media(settings, workspace_id, "9000000000000000001", video, "synthetic-test-owned-v2")
    assert client.get(lookup).json()["run"] is None
