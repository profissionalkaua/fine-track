import os
import subprocess

import imageio_ffmpeg
import pytest


@pytest.mark.skipif(not os.environ.get("PULSO_TEST_WHISPER_PATH"), reason="Optional local weights not selected")
def test_offline_transcription_does_not_invent_speech_in_silence(tmp_path):
    from pulso.adapters.media_signals import transcribe

    audio = tmp_path / "silence.wav"
    subprocess.run(
        [imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-f", "lavfi", "-i",
         "anullsrc=r=16000:cl=mono", "-t", "2", "-y", str(audio)],
        check=True, timeout=30,
    )
    result = transcribe(audio, os.environ["PULSO_TEST_WHISPER_PATH"])
    assert result["state"] == "completed"
    assert result["language"] == "pt"
    assert result["segments"] == []


@pytest.mark.skipif(not os.environ.get("PULSO_TEST_TESSERACT_PATH"), reason="Optional OCR not selected")
def test_local_ocr_reads_portuguese_title_with_original_timestamp(tmp_path):
    from pathlib import Path

    from PIL import Image, ImageDraw, ImageFont

    from pulso.adapters.media_signals import extract_text

    picture = Image.new("RGB", (1200, 240), "white")
    ImageDraw.Draw(picture).text(
        (40, 50), "RECEITA CASEIRA", fill="black",
        font=ImageFont.truetype("arial.ttf" if os.name == "nt" else "DejaVuSans.ttf", 96),
    )
    path = tmp_path / "title.png"
    picture.save(path)
    result = extract_text(
        [{"path": Path(path), "timestamp_ms": 1500}],
        executable=os.environ["PULSO_TEST_TESSERACT_PATH"], language="por+eng",
    )
    assert result["state"] == "completed"
    assert result["segments"] == [{"timestamp_ms": 1500, "text": "RECEITA CASEIRA"}]


@pytest.mark.skipif(not os.environ.get("PULSO_TEST_POSE_PATH"), reason="Optional pose weights not selected")
def test_local_pose_model_loads_from_unicode_path_without_inventing_people(tmp_path):
    from pathlib import Path

    from pulso.adapters.media_signals import estimate_pose

    directory = tmp_path / "mídia"
    directory.mkdir()
    model = directory / "postura.task"
    model.write_bytes(Path(os.environ["PULSO_TEST_POSE_PATH"]).read_bytes())
    video = directory / "blue.mp4"
    subprocess.run(
        [imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-f", "lavfi", "-i",
         "color=c=blue:s=160x120:d=2", "-y", str(video)], check=True, timeout=30,
    )
    result = estimate_pose(video, str(model), 2000)
    assert result["state"] == "completed"
    assert result["sampled_frames"] == 8
    assert result["segments"] == []


def test_authorized_synthetic_media_keeps_original_timestamps_and_honest_absence(tmp_path):
    from pulso.adapters.media import MediaAnalyzer
    from pulso.config import Settings

    video = tmp_path / "synthetic.mp4"
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
    settings = Settings.testing()
    analyzer = MediaAnalyzer(settings, media_root=tmp_path, temp_root=tmp_path / "work")
    result = analyzer.analyze(video, caption="Uma imagem sintética para teste")
    assert result["duration_ms"] == 2000
    assert result["state"] == "partial"
    assert result["segments"] == []
    assert result["frames"][0]["timestamp_ms"] == 0
    assert result["frames"][-1]["timestamp_ms"] < 2000
    assert result["transcription"]["state"] == "unavailable"
    assert list((tmp_path / "work").iterdir()) == []


def test_media_rejects_file_outside_authorized_root(tmp_path):
    from pulso.adapters.media import MediaAnalyzer
    from pulso.config import Settings

    outside = tmp_path / "outside.mp4"
    outside.write_bytes(b"untrusted")
    analyzer = MediaAnalyzer(
        Settings.testing(), media_root=tmp_path / "authorized", temp_root=tmp_path / "work"
    )
    with pytest.raises(ValueError, match="autorizado"):
        analyzer.analyze(outside)
