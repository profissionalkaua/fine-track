import json
from functools import partial

import httpx
from test_runs import generated


def test_text_generation_accepts_dense_pose_evidence_within_provider_context(monkeypatch, settings):
    from pulso.adapters.ollama import OllamaGenerator

    def provider(request):
        payload = json.loads(request.content)
        if len(payload["messages"][-1]["content"]) > 24000:
            return httpx.Response(400, json={"error": "request exceeds available context size"})
        return httpx.Response(200, json={"message": {"content": json.dumps(generated(1))}})

    monkeypatch.setattr(httpx, "Client", partial(httpx.Client, transport=httpx.MockTransport(provider)))
    settings.ollama_model = "external-fixture"
    reference = {
        "id": "9000000000000000001",
        "description": "Explicação educativa",
        "hashtags": [],
        "transcript": "Uma demonstração sobre números binários.",
        "analise_visual": {
            "state": "completed",
            "segments": [{"start_ms": 0, "end_ms": 129000, "people_count": 1}],
            "pose": {
                "state": "completed",
                "segments": [
                    {
                        "start_ms": i * 250,
                        "end_ms": (i + 1) * 250,
                        "people_detected": 1,
                        "confidence": 0.8,
                        "raised_wrists": 1,
                        "limitations": "Estimativa de postura; cortes e oclusões reduzem a confiança.",
                    }
                    for i in range(516)
                ],
            },
        },
    }
    result = OllamaGenerator(settings).generate([reference], {}, 1)
    assert result["ideas"][0]["reference_ids"] == [reference["id"]]
    assert len(reference["analise_visual"]["pose"]["segments"]) == 516


def test_vision_accepts_dense_pose_evidence_without_losing_temporal_extent(monkeypatch, settings, tmp_path):
    from pulso.adapters.media import MediaAnalyzer

    def provider(request):
        prompt = json.loads(json.loads(request.content)["messages"][-1]["content"])
        if len(json.dumps(prompt)) > 16000:
            return httpx.Response(400, json={"error": "request exceeds available context size"})
        segments = prompt["pose_signals"]["segments"]
        assert segments[0]["start_ms"] == 0
        assert segments[-1]["end_ms"] == 129000
        return httpx.Response(200, json={"message": {"content": json.dumps({"segments": []})}})

    monkeypatch.setattr(httpx, "Client", partial(httpx.Client, transport=httpx.MockTransport(provider)))
    pose = {
        "state": "completed",
        "sampled_frames": 516,
        "segments": [
            {
                "start_ms": i * 250,
                "end_ms": (i + 1) * 250,
                "people_detected": 1,
                "confidence": 0.8,
                "raised_wrists": 1,
                "limitations": "Estimativa de postura; cortes e oclusões reduzem a confiança.",
            }
            for i in range(516)
        ],
    }
    frame = tmp_path / "frame.jpg"
    frame.write_bytes(b"external-provider-fixture")
    settings.vision_model = "external-fixture"
    result = MediaAnalyzer(settings).describe(
        [{"path": frame, "timestamp_ms": 0}],
        "Explicação educativa",
        129000,
        pose,
        {"segments": []},
    )
    assert result.segments == []
    assert len(pose["segments"]) == 516
