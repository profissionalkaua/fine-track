"""Check HTTP -> durable outbox -> RabbitMQ -> worker without models or live collection."""

import http.cookiejar
import json
import os
import time
import urllib.request
import uuid

base = "http://127.0.0.1:3000/api"
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def request(path, body=None, headers=None):
    payload = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        base + path, data=payload, headers={"Content-Type": "application/json", **(headers or {})}
    )
    with opener.open(req, timeout=15) as response:
        return json.load(response)


identity = request(
    "/v1/auth/login", {"email": "smoke@pulso.local", "password": os.environ["PULSO_SMOKE_PASSWORD"]}
)
run = request(
    "/v1/runs", {"scope": "feed"},
    {"X-CSRF-Token": identity["csrf_token"], "Idempotency-Key": str(uuid.uuid4())},
)
deadline = time.monotonic() + 90
while time.monotonic() < deadline:
    result = request(f"/v1/runs/{run['id']}")
    if result["state"] == "partial":
        assert result["errors"][0]["code"] == "insufficient_references"
        print("HTTP, outbox, broker and worker completed an isolated analysis.")
        break
    if result["state"] in {"failed", "cancelled", "completed"}:
        raise SystemExit(f"Unexpected smoke result: {result['state']}")
    time.sleep(2)
else:
    raise SystemExit("Worker did not consume the durable job within 90 seconds.")
