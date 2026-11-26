"""Guest-only source bridge, executed by the optional isolated F2 interpreter."""

import json
import logging
import sys
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from importlib.metadata import version

from .public_network import public_addresses, safe_public_url


def collect(request):
    # Imported only in the isolated environment, preserving application dependency pins.
    from curl_cffi import CurlOpt, requests
    from f2.apps.tiktok.model import BaseRequestModel
    from f2.apps.tiktok.utils import ClientConfManager, XGnarlyManager

    source, reference = request["source"], request["reference"]
    count = max(1, min(int(request["count"]), 50))
    user_agent = ClientConfManager.user_agent()
    params = BaseRequestModel().model_dump()
    address = public_addresses("www.tiktok.com")[0]
    address = f"[{address}]" if ":" in address else address

    with requests.Session(
        impersonate="chrome",
        headers={"User-Agent": user_agent, "Referer": "https://www.tiktok.com/"},
        curl_options={CurlOpt.RESOLVE: [f"www.tiktok.com:443:{address}"], CurlOpt.PROXY: ""},
    ) as client:

        def get(path, extra):
            endpoint = XGnarlyManager.model_2_endpoint(
                user_agent, "https://www.tiktok.com/api/" + path, params | extra, cookie=""
            )
            body = bytearray()

            def receive(chunk):
                if len(body) + len(chunk) > 8_000_000:
                    return 0
                body.extend(chunk)
                return len(chunk)

            try:
                response = client.get(
                    safe_public_url(endpoint), timeout=20, allow_redirects=False, content_callback=receive
                )
            except requests.RequestsError:
                raise SourceFailure("unavailable") from None
            if response.status_code == 429:
                raise SourceFailure("rate_limited", retry_delay(response.headers.get("Retry-After")))
            if response.status_code in {401, 403}:
                raise SourceFailure("blocked")
            if response.status_code != 200:
                raise SourceFailure("unavailable")
            data = json.loads(body)
            status = data.get("statusCode", data.get("status_code"))
            if status == 2483:
                raise SourceFailure("blocked")
            if status != 0:
                raise SourceFailure("unavailable")
            return data

        if source != "trending":
            get("recommend/item_list/", {"count": 1})
        if source == "trending":
            data = get("recommend/item_list/", {"count": count})
        elif source == "hashtag":
            tag = get("challenge/detail/", {"challengeName": reference})["challengeInfo"]["challenge"]["id"]
            data = get("challenge/item_list/", {"challengeID": tag, "count": count, "cursor": 0})
        elif source in {"creator", "profile"}:
            profile = get("user/detail/", {"uniqueId": reference, "secUid": ""})
            if source == "profile":
                return {"version": version("f2"), "data": profile}
            sec_uid = profile["userInfo"]["user"]["secUid"]
            data = get("post/item_list/", {"secUid": sec_uid, "count": count, "cursor": 0})
        else:
            raise SourceFailure("unavailable")
        items = data.get("itemList")
        if not isinstance(items, list):
            raise SourceFailure("unavailable")
        return {"version": version("f2"), "data": items[:count]}


class SourceFailure(Exception):
    def __init__(self, kind, retry_after=None):
        super().__init__(kind)
        self.retry_after = retry_after


def retry_delay(value):
    try:
        if value and value.isdigit():
            return int(value)
        return max(0, (parsedate_to_datetime(value) - datetime.now(UTC)).total_seconds())
    except (TypeError, ValueError, OverflowError):
        return 300


if __name__ == "__main__":
    logging.disable(logging.CRITICAL)
    try:
        result = collect(json.loads(sys.stdin.read(4096)))
    except SourceFailure as exc:
        result = {"error": str(exc), "retry_after": exc.retry_after}
    except Exception:
        result = {"error": "unavailable"}
    print(json.dumps(result, ensure_ascii=True))
