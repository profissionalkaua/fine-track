import json
import subprocess
from functools import partial

import httpx
import imageio_ffmpeg
import pytest

from pulso.adapters.media import MediaAnalyzer
from pulso.adapters.media_signals import wrist_changes


@pytest.mark.parametrize("exhaust_budget", [False, True])
def test_sparse_frames_cannot_publish_full_clip_as_static(tmp_path, monkeypatch, settings, exhaust_budget):
    video = tmp_path / "moving.mp4"
    subprocess.run(
        [
            imageio_ffmpeg.get_ffmpeg_exe(),
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=160x120:rate=10:duration=3",
            str(video),
        ],
        check=True,
    )
    segment = dict(
        start_ms=0,
        end_ms=3000,
        movement="Nenhum movimento.",
        scene="Painel de cores",
        lighting=None,
        camera="Estática",
        clothing=None,
        dance_style=None,
        people_count=0,
        confidence=0.99,
    )
    elapsed = [0]
    monkeypatch.setattr("pulso.adapters.media.time.monotonic", lambda: elapsed[0])

    def respond(request):
        if exhaust_budget:
            elapsed[0] += 181
        return httpx.Response(200, json={"message": {"content": json.dumps({"segments": [segment]})}})

    transport = httpx.MockTransport(respond)
    monkeypatch.setattr(httpx, "Client", partial(httpx.Client, transport=transport))
    settings.vision_model = "fixture"
    settings.vision_max_frames = 2
    result = MediaAnalyzer(settings, tmp_path, tmp_path / "work").analyze(video)
    expected_times = (
        result["vision_frame_timestamps_ms"][:1] if exhaust_budget else result["vision_frame_timestamps_ms"]
    )
    assert [s["start_ms"] for s in result["segments"]] == expected_times
    assert result["state"] == ("partial" if exhaust_budget else "completed")
    assert all(s["end_ms"] - s["start_ms"] <= 100 and s["camera"] is None for s in result["segments"])
    assert all(s["movement"] is None for s in result["segments"])
    assert any(sample["mean_luma_delta"] > 0 for sample in result["frame_changes"])


def test_ocr_keeps_reliable_words_and_discards_low_confidence_noise(tmp_path, monkeypatch):
    from pulso.adapters.media_signals import extract_text

    def tesseract(command, **kwargs):
        text = (
            "level\tconf\ttext\n5\t12.1\tXx\n5\t91.7\tReceita\n5\t94.2\t42\n"
            if command[-1] == "tsv"
            else "Xx Receita 42"
        )
        return subprocess.CompletedProcess(command, 0, stdout=text)

    monkeypatch.setattr(subprocess, "run", tesseract)
    result = extract_text([{"timestamp_ms": 500, "path": tmp_path / "frame.jpg"}], executable="fixture")
    assert result["segments"] == [{"timestamp_ms": 500, "text": "Receita 42"}]


def test_wrist_changes_require_adjacent_visible_single_person_samples_in_same_shot():
    before = dict(start_ms=0, confidence=0.9, people_detected=1, raised_wrists=0)
    after = dict(start_ms=250, confidence=0.9, people_detected=1, raised_wrists=1)
    assert wrist_changes([before, after], []) == [
        dict(start_ms=0, end_ms=250, raised_before=0, raised_after=1)
    ]
    assert wrist_changes([before, after], [125]) == []
    assert wrist_changes([before, {**after, "start_ms": 500}], []) == []
    assert wrist_changes([before, {**after, "confidence": 0.7}], []) == []
    assert wrist_changes([before, {**after, "people_detected": 2}], []) == []
