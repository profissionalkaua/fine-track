import json
import subprocess
import sys
from types import SimpleNamespace

import pytest

from pulso.adapters.tiktok import SourceError, TikTokCollector


@pytest.mark.parametrize("failure", [None, "rate_limited", "oversized", "private_dns"])
def test_guest_bridge_bootstraps_public_session_before_reading_creator(monkeypatch, failure):
    from pulso.adapters import f2_guest

    calls = []

    class Session:
        def __init__(self, **kwargs):
            assert "Cookie" not in kwargs["headers"]
            assert kwargs["curl_options"][10004] == ""

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def get(self, endpoint, **kwargs):
            calls.append(endpoint)
            if failure == "rate_limited":
                return SimpleNamespace(status_code=429, headers={"Retry-After": "900"})
            if failure == "oversized":
                assert kwargs["content_callback"](b"x" * 8_000_001) == 0
                raise RuntimeError("Transfer aborted")
            if endpoint.endswith("user/detail/"):
                assert len(calls) == 2
                data = {"statusCode": 0, "userInfo": {"user": {"secUid": "public-id"}}}
            else:
                data = {"statusCode": 0, "itemList": [{"id": "123"}]}
            body = json.dumps(data).encode()
            assert kwargs["content_callback"](body) == len(body)
            return SimpleNamespace(status_code=200, headers={})

    ip = "127.0.0.1" if failure == "private_dns" else "8.8.8.8"
    monkeypatch.setattr("socket.getaddrinfo", lambda *a, **kw: [(2, 1, 6, "", (ip, 443))])
    monkeypatch.setitem(
        sys.modules,
        "curl_cffi",
        SimpleNamespace(
            requests=SimpleNamespace(Session=Session, RequestsError=RuntimeError),
            CurlOpt=SimpleNamespace(RESOLVE=10203, PROXY=10004),
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "f2.apps.tiktok.model",
        SimpleNamespace(BaseRequestModel=lambda: SimpleNamespace(model_dump=lambda: {})),
    )
    monkeypatch.setitem(
        sys.modules,
        "f2.apps.tiktok.utils",
        SimpleNamespace(
            ClientConfManager=SimpleNamespace(user_agent=lambda: "fixture"),
            XGnarlyManager=SimpleNamespace(model_2_endpoint=lambda ua, endpoint, params, cookie: endpoint),
        ),
    )
    monkeypatch.setattr(f2_guest, "version", lambda name: "0.0.1.7")
    request = {"source": "creator", "reference": "tiktok", "count": 1}
    if failure == "private_dns":
        with pytest.raises(ValueError, match="interno"):
            f2_guest.collect(request)
        assert calls == []
        return
    if failure:
        with pytest.raises(f2_guest.SourceFailure) as error:
            f2_guest.collect(request)
        assert str(error.value) == ("rate_limited" if failure == "rate_limited" else "unavailable")
        if failure == "rate_limited":
            assert error.value.retry_after == 900
        return
    result = f2_guest.collect(request)
    assert result["data"] == [{"id": "123"}]
    assert calls == [
        "https://www.tiktok.com/api/" + path
        for path in ["recommend/item_list/", "user/detail/", "post/item_list/"]
    ]


def test_f2_collector_uses_existing_normalization_and_collection_gate(settings, monkeypatch):
    settings.f2_python_path = "isolated-python"
    calls = []

    def run(command, **kwargs):
        calls.append(json.loads(kwargs["input"]))
        return subprocess.CompletedProcess(
            command,
            0,
            json.dumps(
                {
                    "version": "0.0.1.7",
                    "data": [
                        {
                            "id": "123",
                            "author": {"id": "42", "uniqueId": "tiktok"},
                            "createTime": 1700000000,
                            "desc": "Exemplo público",
                            "stats": {"playCount": 5},
                        }
                    ],
                }
            ),
        )

    monkeypatch.setattr("pulso.adapters.tiktok.subprocess.run", run)
    collector = TikTokCollector(settings)
    with pytest.raises(SourceError):
        collector.collect("trending", count=1)
    assert calls == []
    settings.collection_enabled = True
    records = collector.collect("trending", count=1)
    assert calls == [{"source": "trending", "reference": None, "count": 1}]
    assert records[0]["country"] is None
    assert records[0]["synthetic"] is False
    assert records[0]["snapshots"][0]["source"] == "f2-public-web"
    assert records[0]["geo_evidence"]["library_version"] == "f2:0.0.1.7"


@pytest.mark.parametrize(
    "payload",
    [{"error": "blocked"}, {"error": "rate_limited", "retry_after": 900}, {"data": "invalid"}, [], None],
)
def test_f2_collector_surfaces_source_failures(settings, monkeypatch, payload):
    settings.collection_enabled = True
    settings.f2_python_path = "isolated-python"
    monkeypatch.setattr(
        "pulso.adapters.tiktok.subprocess.run",
        lambda *a, **kw: subprocess.CompletedProcess(a[0], 0, json.dumps(payload)),
    )
    with pytest.raises(SourceError) as error:
        TikTokCollector(settings).collect("trending", count=1)
    assert error.value.kind == (
        payload.get("error", "unavailable") if isinstance(payload, dict) else "unavailable"
    )
    if isinstance(payload, dict) and payload.get("error") == "rate_limited":
        assert error.value.retry_after == 900
