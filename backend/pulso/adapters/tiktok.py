import asyncio
import ipaddress
import re
import socket
from datetime import UTC, datetime
from importlib.metadata import version
from typing import Protocol
from urllib.parse import urlsplit

import pycountry

from ..db import now
from ..feed import normalize


class SourceError(Exception):
    def __init__(self, message="Fonte indisponível.", kind="unavailable", retry_after=None):
        super().__init__(message)
        self.kind = kind
        self.retry_after = retry_after


class Collector(Protocol):
    def collect(self, source: str, reference: str | None, count: int) -> list[dict]: ...
    def profile(self, handle: str) -> dict: ...


def parse_handle(value: str):
    value = value.strip()
    if "://" in value:
        url = urlsplit(value)
        if (
            url.scheme != "https"
            or url.hostname not in {"www.tiktok.com", "tiktok.com"}
            or url.username
            or url.password
            or url.port not in {None, 443}
            or url.query
            or url.fragment
        ):
            raise ValueError("Use um usuário ou URL https://www.tiktok.com/@perfil.")
        value = url.path.rstrip("/")
        if not value.startswith("/@") or "/" in value[2:]:
            raise ValueError("Informe a URL do perfil, sem caminhos adicionais.")
        value = value[2:]
    else:
        value = value.removeprefix("@")
    if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.]{0,23}", value):
        raise ValueError("Usuário do TikTok inválido.")
    return value.lower()


def safe_public_url(value: str, *, media=False):
    url = urlsplit(value)
    suffixes = (
        "tiktok.com",
        "tiktokcdn.com",
        "tiktokcdn-us.com",
        "ttwstatic.com",  # Bootstrap assets requested by the public TikTok page.
        "byteoversea.com",
        "ibytedtos.com",
        "byteimg.com",
    )
    host = url.hostname or ""
    if (
        url.scheme != "https"
        or url.username
        or url.password
        or url.port not in {None, 443}
        or not any(host == suffix or host.endswith("." + suffix) for suffix in suffixes)
    ):
        raise ValueError("Destino externo não permitido.")
    for result in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM):
        if not ipaddress.ip_address(result[4][0]).is_global:
            raise ValueError("Endereço interno não permitido.")
    return value


def normalize_video(raw: dict, observed_at=None, source="tiktok-api", source_reference=None):
    video_id = str(raw.get("id", ""))
    if not re.fullmatch(r"\d{1,32}", video_id):
        raise ValueError("ID de vídeo ausente ou inválido.")
    author = raw.get("author") or {}
    handle = parse_handle(author.get("uniqueId", ""))
    creator_id = str(author.get("id", ""))
    if not creator_id:
        raise ValueError("ID de criador ausente.")
    country = raw.get("region")
    country = country if isinstance(country, str) and pycountry.countries.get(alpha_2=country) else None
    tags: dict[str, str] = {}
    for item in raw.get("challenges") or []:
        tag = item.get("title", "").strip().lstrip("#")
        if tag:
            tags.setdefault(normalize(tag), tag)
    for tag in re.findall(r"#([^\W_][\w]*)", raw.get("desc") or "", re.UNICODE):
        tags.setdefault(normalize(tag), tag)
    stats = raw.get("stats") or {}

    def counter(key):
        value = stats.get(key)
        return (
            value
            if isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 2**63 - 1
            else None
        )

    observed_at = observed_at or now()
    duration = (raw.get("video") or {}).get("duration")
    return {
        "id": video_id,
        "creator_id": creator_id,
        "handle": handle,
        "description": str(raw.get("desc") or "")[:20000],
        "url": f"https://www.tiktok.com/@{handle}/video/{video_id}",
        # Remote thumbnails are optional; only the authorized media adapter fetches external assets.
        "thumbnail": None,
        "published_at": datetime.fromtimestamp(int(raw["createTime"]), UTC).isoformat(),
        "country": country,
        "geo_evidence": {
            "kind": "observed" if country else "unknown",
            "reason": "Campo region retornado pela fonte" if country else "Fonte sem país verificável",
            "confidence": 1 if country else 0,
            "source": source,
            "reference": source_reference,
            "adapter_version": "tiktok-v1",
        },
        "categories": [],
        "hashtags": list(tags.values()),
        "duration": duration if isinstance(duration, (int, float)) and duration > 0 else None,
        "synthetic": False,
        "snapshots": [
            {
                "observed_at": observed_at.isoformat(),
                "views": counter("playCount"),
                "likes": counter("diggCount"),
                "comments": counter("commentCount"),
                "shares": counter("shareCount"),
                "source": source,
            }
        ],
    }


class TikTokCollector:
    def __init__(self, settings):
        self.settings = settings

    def collect(self, source, reference=None, count=40):
        return asyncio.run(self._request(source, reference, min(count, 50)))

    def profile(self, handle):
        return asyncio.run(self._request("profile", parse_handle(handle), 1))

    async def _request(self, source, reference, count):
        if not self.settings.collection_enabled:
            raise SourceError("A coleta externa está desativada. Configure o acesso autorizado.")
        try:
            from TikTokApi import TikTokApi
        except ImportError:
            raise SourceError("Instale as dependências opcionais do coletor e o Chromium.") from None
        blocked = False

        async def page_factory(context):
            page = await context.new_page()

            async def route_request(route):
                try:
                    safe_public_url(route.request.url)
                except (ValueError, OSError):
                    await route.abort()
                    return
                await route.continue_()

            await context.route("**/*", route_request)
            return page

        try:
            async with TikTokApi() as api:
                await api.create_sessions(
                    num_sessions=1,
                    headless=True,
                    sleep_after=3,
                    ms_tokens=[self.settings.ms_token] if self.settings.ms_token else None,
                    enable_session_recovery=False,
                    page_factory=page_factory,
                )
                if source == "profile":
                    data = await api.user(username=reference).info()
                    user = data.get("userInfo", {}).get("user", {})
                    if not user.get("id"):
                        raise SourceError("O perfil não pôde ser confirmado.", "unavailable")
                    return {
                        "id": str(user["id"]),
                        "handle": parse_handle(user["uniqueId"]),
                        "name": str(user.get("nickname") or user["uniqueId"]),
                        "available": not bool(user.get("privateAccount")),
                        "adapter_version": version("TikTokApi"),
                    }
                if source == "trending":
                    stream = api.trending.videos(count=count)
                elif source == "hashtag":
                    if not reference or not re.fullmatch(r"[\w]{1,100}", reference):
                        raise ValueError("Hashtag de descoberta inválida.")
                    stream = api.hashtag(name=reference).videos(count=count)
                elif source == "creator":
                    stream = api.user(username=parse_handle(reference)).videos(count=count)
                else:
                    raise ValueError("Fonte desconhecida.")
                records = []
                async for video in stream:
                    record = normalize_video(video.as_dict, source_reference=f"{source}:{reference or ''}")
                    record["geo_evidence"]["library_version"] = version("TikTokApi")
                    records.append(record)
                    if len(records) >= count:
                        break
                return records
        except SourceError:
            raise
        except Exception as exc:
            message = str(exc).lower()
            blocked = any(word in message for word in ["captcha", "403", "challenge", "blocked"])
            rate_limited = "429" in message or "rate limit" in message
            raise SourceError(
                "A fonte bloqueou o acesso." if blocked else "A fonte não respondeu à coleta.",
                "blocked" if blocked else "rate_limited" if rate_limited else "unavailable",
                300 if rate_limited else None,
            ) from None
