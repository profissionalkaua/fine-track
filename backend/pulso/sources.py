from datetime import timedelta
from hashlib import sha256

from sqlalchemy import text

from .adapters.tiktok import SourceError
from .db import session_for
from .models import CollectionCache, SourceHealth


def fetch_shared(app, source, reference=None, count=30):
    """Share public observations and serialize outbound browser access across workers."""
    time = app.state.clock()
    hours = {"trending": 2, "hashtag": 4, "creator": 6, "profile": 6}[source]
    key = sha256(f"{source}:{reference or ''}:{int(time.timestamp() // (hours * 3600))}".encode()).hexdigest()
    failure = None
    value = None
    with session_for(app.state.engine) as db, db.begin():
        health = db.get(SourceHealth, "tiktok")
        if health and health.suspended:
            raise SourceError("Fonte suspensa após bloqueio. Aguardando revisão do operador.", "blocked")
        if health and health.retry_at and health.retry_at > time:
            raise SourceError(
                "Fonte aguardando a próxima tentativa.",
                "rate_limited",
                int((health.retry_at - time).total_seconds()),
            )
        cached = db.get(CollectionCache, key)
        if cached and cached.expires_at > time:
            return cached.payload["value"]
        acquired = db.execute(text("SELECT pg_try_advisory_xact_lock(7341902)")).scalar()
        if not acquired:
            raise SourceError(
                "Outra coleta está em andamento. Aguardando o próximo intervalo.", "unavailable", 30
            )
        # The shared lock also covers different source routes, enforcing one outbound browser at a time.
        cached = db.get(CollectionCache, key, populate_existing=True)
        if cached and cached.expires_at > time:
            return cached.payload["value"]
        try:
            value = (
                app.state.collector.profile(reference)
                if source == "profile"
                else app.state.collector.collect(source, reference, count)
            )
        except SourceError as exc:
            failure = exc
            health = health or SourceHealth(source="tiktok")
            health.suspended = exc.kind == "blocked"
            health.reason = str(exc)
            health.retry_at = time + timedelta(seconds=exc.retry_after or 60)
            db.add(health)
        if failure is None:
            db.merge(
                CollectionCache(key=key, expires_at=time + timedelta(hours=hours), payload={"value": value})
            )
    if failure:
        raise failure
    return value
