"""Optional offline audio, text and pose extractors. Each reports its own absence."""

import csv
import shutil
import subprocess
from bisect import bisect_right
from pathlib import Path


def transcribe(path: Path, model_path: str):
    if not model_path or not Path(model_path).exists():
        return {
            "state": "unavailable",
            "reason": "Modelo de transcrição local não configurado.",
            "segments": [],
        }
    try:
        import av
        from faster_whisper import WhisperModel

        with av.open(str(path)) as media:
            if not media.streams.audio:
                return {"state": "unavailable", "reason": "Mídia sem faixa de áudio.", "segments": []}
        model = WhisperModel(model_path, device="cpu", compute_type="int8", local_files_only=True)
        segments, info = model.transcribe(str(path), language="pt", vad_filter=True)
        return {
            "state": "completed",
            "model": Path(model_path).name,
            "language": info.language,
            "segments": [
                {"start_ms": round(s.start * 1000), "end_ms": round(s.end * 1000), "text": s.text.strip()}
                for s in segments
            ],
        }
    except (ImportError, RuntimeError, ValueError):
        return {"state": "unavailable", "reason": "Transcrição indisponível neste ambiente.", "segments": []}


def extract_text(frames, executable="", language="por+eng"):
    executable = executable or shutil.which("tesseract")
    if not executable:
        return {"state": "unavailable", "reason": "OCR local não instalado.", "segments": []}
    segments = []
    for frame in frames:
        try:
            result = subprocess.run(
                [executable, str(frame["path"]), "stdout", "-l", language, "--psm", "11", "tsv"],
                capture_output=True,
                timeout=20,
                check=True,
                encoding="utf8",
                errors="replace",
            )
            words = csv.DictReader(result.stdout.splitlines(), delimiter="\t", quoting=csv.QUOTE_NONE)
            text = " ".join(
                word["text"].strip()
                for word in words
                if word["level"] == "5"
                and float(word["conf"]) >= 85
                and any(c.isalnum() for c in word["text"])
            )[:5000]
            if text:
                segments.append({"timestamp_ms": frame["timestamp_ms"], "text": text})
        except (subprocess.SubprocessError, OSError):
            return {"state": "partial", "reason": "OCR falhou em um ou mais quadros.", "segments": segments}
    return {"state": "completed", "segments": segments}


def estimate_pose(path: Path, model_path: str, duration_ms: int):
    if not model_path or not Path(model_path).exists():
        return {"state": "unavailable", "reason": "Modelo de postura local não configurado.", "segments": []}
    try:
        import cv2
        import mediapipe as mp
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision

        options = vision.PoseLandmarkerOptions(
            # Native model path loading on Windows loses non-ASCII user/directory names.
            base_options=python.BaseOptions(model_asset_buffer=Path(model_path).read_bytes()),
            running_mode=vision.RunningMode.VIDEO,
            num_poses=4,
        )
        segments = []
        sampled_frames = 0
        capture = cv2.VideoCapture(str(path))
        try:
            with vision.PoseLandmarker.create_from_options(options) as detector:
                previous = None
                for timestamp in range(0, duration_ms, 250):
                    capture.set(cv2.CAP_PROP_POS_MSEC, timestamp)
                    ok, frame = capture.read()
                    if not ok:
                        break
                    sampled_frames += 1
                    image = mp.Image(
                        image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    )
                    result = detector.detect_for_video(image, timestamp)
                    poses = result.pose_landmarks
                    if not poses:
                        previous = None
                        continue
                    pose = poses[0]
                    visible = min(p.visibility or 0 for p in [pose[11], pose[12], pose[15], pose[16]])
                    signal = {
                        "start_ms": timestamp,
                        "end_ms": min(timestamp + 250, duration_ms),
                        "people_detected": len(poses),
                        "confidence": visible,
                        "raised_wrists": sum(pose[w].y < pose[s].y for w, s in [(15, 11), (16, 12)]),
                        "limitations": "Estimativa de postura; cortes e oclusões reduzem a confiança.",
                    }
                    if previous is not None:
                        signal["left_wrist_displacement"] = abs(pose[15].x - previous[15].x) + abs(
                            pose[15].y - previous[15].y
                        )
                        signal["right_wrist_displacement"] = abs(pose[16].x - previous[16].x) + abs(
                            pose[16].y - previous[16].y
                        )
                    segments.append(signal)
                    previous = pose
        finally:
            capture.release()
        if not sampled_frames:
            return {"state": "unavailable", "reason": "Nenhum quadro pôde ser decodificado.", "segments": []}
        return {
            "state": "completed",
            "model": Path(model_path).name,
            "sampled_frames": sampled_frames,
            "segments": segments,
        }
    except (ImportError, RuntimeError, ValueError, OSError):
        return {"state": "unavailable", "reason": "Análise de postura indisponível.", "segments": []}


def wrist_changes(segments, cut_times):
    """Compare visible wrists in adjacent single-person samples within one shot."""
    events = []
    for before, after in zip(segments, segments[1:], strict=False):
        start, end = before["start_ms"], after["start_ms"]
        if (
            end - start != 250
            or min(before["confidence"], after["confidence"]) < 0.8
            or before["people_detected"] != 1
            or after["people_detected"] != 1
            or bisect_right(cut_times, start) != bisect_right(cut_times, end)
            or before["raised_wrists"] == after["raised_wrists"]
        ):
            continue
        events.append(
            {
                "start_ms": start,
                "end_ms": end,
                "raised_before": before["raised_wrists"],
                "raised_after": after["raised_wrists"],
            }
        )
    return events
