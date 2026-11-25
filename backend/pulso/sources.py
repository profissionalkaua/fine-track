from datetime import timedelta
from hashlib import sha256

from sqlalchemy import text

from .adapters.tiktok import SourceError
from .db import session_for
from .models import CollectionCache


def fetch_shared(app, source, reference=None, count=30):
    """Share public observations and serialize outbound browser access across workers."""
    time = app.state.clock()
    hours = {"trending": 2, "hashtag": 4, "creator": 6, "profile": 6}[source]
    key = sha256(f"{source}:{reference or ''}:{int(time.timestamp() // (hours * 3600))}".encode()).hexdigest()
    with session_for(app.state.engine) as db, db.begin():
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
        value = (
            app.state.collector.profile(reference)
            if source == "profile"
            else app.state.collector.collect(source, reference, count)
        )
        db.merge(CollectionCache(key=key, expires_at=time + timedelta(hours=hours), payload={"value": value}))
        return value
