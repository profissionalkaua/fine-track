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


def test_still_provider_receives_one_image_and_only_its_timestamp(monkeypatch, settings, tmp_path):
    from pulso.adapters.media import MediaAnalyzer

    def provider(request):
        message = json.loads(request.content)["messages"][-1]
        assert len(message["images"]) == 1
        assert json.loads(message["content"]) == {"start_ms": 1750, "end_ms": 1751}
        return httpx.Response(200, json={"message": {"content": json.dumps({"segments": []})}})

    monkeypatch.setattr(httpx, "Client", partial(httpx.Client, transport=httpx.MockTransport(provider)))
    frame = tmp_path / "frame.jpg"
    frame.write_bytes(b"external-provider-fixture")
    assert MediaAnalyzer(settings).describe_frame({"path": frame, "timestamp_ms": 1750}).segments == []
