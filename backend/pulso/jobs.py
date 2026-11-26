"""Durable scheduling and an idempotent executor shared by Celery and integration tests."""

from datetime import timedelta
from hashlib import sha256
from secrets import randbelow

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert

from .adapters.tiktok import SourceError
from .db import session_for, uid
from .models import Job, Outbox, SourceHealth


def workspace(db, workspace_id):
    db.execute(text("SELECT set_config('pulso.workspace_id', :id, true)"), {"id": workspace_id})


def enqueue(db, workspace_id, kind, key, payload, time):
    queue = {
        "collect": "collection",
        "profile": "collection",
        "classify": "classification",
        "generate": "generation",
    }.get(kind, "analysis")
    if kind == "run" and payload.get("media_required"):
        queue = "multimodal"
    job_id = uid()
    db.execute(
        insert(Job)
        .values(
            id=job_id,
            workspace_id=workspace_id,
            key=key,
            kind=kind,
            payload=payload,
            state="queued",
            attempts=0,
            not_before=time,
        )
        .on_conflict_do_nothing(index_elements=["workspace_id", "key"])
    )
    job = db.scalar(select(Job).where(Job.workspace_id == workspace_id, Job.key == key))
    db.execute(
        insert(Outbox)
        .values(
            id=uid(),
            job_id=job.id,
            workspace_id=workspace_id,
            queue=queue,
            not_before=time,
        )
        .on_conflict_do_nothing(index_elements=["job_id"])
    )
    return job


def execute_job(app, job_id, workspace_id):
    time = app.state.clock()
    token = uid()
    with session_for(app.state.engine) as db, db.begin():
        workspace(db, workspace_id)
        job = db.scalar(select(Job).where(Job.id == job_id).with_for_update(skip_locked=True))
        if job is None or job.state in {"completed", "failed", "cancelled"} or job.not_before > time:
            return
        if job.state == "running" and job.lease_until and job.lease_until > time:
            envelope = db.scalar(select(Outbox).where(Outbox.job_id == job.id))
            if envelope:
                envelope.sent_at = None
                envelope.not_before = job.lease_until
            return
        job.state = "running"
        job.attempts += 1
        job.lease_token = token
        job.lease_until = time + timedelta(minutes=15)
        payload, kind = job.payload, job.kind
    try:
        if kind == "collect":
            collect(app, {**payload, "source_job_id": job_id}, workspace_id)
        elif kind == "profile":
            from .creators import resolve_profile

            resolve_profile(app, payload, workspace_id)
        elif kind == "run":
            from .runs import execute_run

            execute_run(app, payload["run_id"], workspace_id)
        elif kind == "generate":
            from .runs import generate_run

            generate_run(app, payload, workspace_id)
        elif kind == "classify":
            from .classification import classify_job

            classify_job(app, payload)
        else:
            raise ValueError("Tipo de job desconhecido.")
    except Exception as exc:
        transient = isinstance(exc, SourceError) and exc.kind in {"unavailable", "rate_limited"}
        with session_for(app.state.engine) as db, db.begin():
            workspace(db, workspace_id)
            job = db.get(Job, job_id)
            if job.lease_token != token:
                return
            job.error = str(exc) if isinstance(exc, SourceError) else "A etapa falhou. Tente novamente."
            job.error_kind = exc.kind if isinstance(exc, SourceError) else "processing_failed"
            if transient and job.attempts < 3:
                job.state = "queued"
                job.not_before = time + timedelta(
                    seconds=max(getattr(exc, "retry_after", 0) or 0, 30 * 2**job.attempts) + randbelow(20)
                )
                outbox = db.scalar(select(Outbox).where(Outbox.job_id == job_id))
                outbox.sent_at = None
                outbox.not_before = job.not_before
            else:
                job.state = "failed"
                if kind in {"run", "generate"}:
                    from .models import Run

                    execution = db.get(Run, payload["run_id"])
                    if execution and execution.state not in {"cancelled", "completed", "partial", "failed"}:
                        execution.state = "failed"
                        execution.errors = [
                            {
                                "stage": "processing",
                                "code": "worker_failed",
                                "message": "A etapa falhou. Retome a análise para tentar novamente.",
                            }
                        ]
            job.lease_until = None
        return
    with session_for(app.state.engine) as db, db.begin():
        workspace(db, workspace_id)
        job = db.get(Job, job_id)
        if job.lease_token == token:
            job.state, job.lease_until = "completed", None


def collect(app, payload, workspace_id):
    from .feed import ingest_records, publish_ranking

    with session_for(app.state.engine) as db:
        health = db.get(SourceHealth, "tiktok")
        if health and health.suspended:
            raise SourceError("Fonte suspensa após bloqueio. Aguardando revisão do operador.", "blocked")
        if health and health.retry_at and health.retry_at > app.state.clock():
            raise SourceError(
                "Fonte aguardando a próxima tentativa.",
                "rate_limited",
                int((health.retry_at - app.state.clock()).total_seconds()),
            )
    mode = payload.get("mode", "all")
    sources: list[tuple[str, str | None]] = [("trending", None)] if mode in {"all", "trending"} else []
    category = payload.get("category") or ""
    terms = [part for part in category.split() if part.isalnum()]
    tags = terms[:2] if terms else ["criatividade", "receitas", "rotina"]
    if mode in {"all", "hashtags"}:
        sources.extend(("hashtag", tag) for tag in tags)
    if mode in {"all", "creators"}:
        from .models import WorkspaceCreator

        with session_for(app.state.engine) as db:
            workspace(db, workspace_id)
            active = set(
                db.scalars(select(WorkspaceCreator.handle).where(WorkspaceCreator.status == "active")).all()
            )
        sources.extend(("creator", handle) for handle in payload.get("handles", [])[:6] if handle in active)
    records = []
    try:
        for source, reference in sources:
            from .sources import fetch_shared

            batch = fetch_shared(app, source, reference)
            records.extend(batch)
            with session_for(app.state.engine) as db, db.begin():
                ingest_records(
                    db, batch, allow_synthetic=app.state.settings.environment in {"development", "test"}
                )
    except SourceError as exc:
        with session_for(app.state.engine) as db, db.begin():
            health = db.get(SourceHealth, "tiktok") or SourceHealth(source="tiktok")
            health.suspended = exc.kind == "blocked"
            health.reason = str(exc)
            health.retry_at = app.state.clock() + timedelta(seconds=exc.retry_after or 60)
            db.add(health)
        raise
    with session_for(app.state.engine) as db, db.begin():
        ingest_records(db, records, allow_synthetic=app.state.settings.environment in {"development", "test"})
        for period in ["day", "week", "month"]:
            publish_ranking(
                db,
                payload["country"],
                period,
                category,
                as_of=app.state.clock(),
                freshness=app.state.settings.latest_snapshot_hours,
            )
        if records:
            workspace(db, workspace_id)
            enqueue(
                db,
                workspace_id,
                "classify",
                f"classify:{payload['source_job_id']}",
                {
                    "video_ids": list({r["id"] for r in records})[:60],
                    "country": payload["country"],
                    "category": category,
                },
                app.state.clock(),
            )


def drain_once(app):
    """Controlled executor for tests and the explicit local worker command."""
    for _ in range(3):
        if not drain_batch(app):
            break


def drain_batch(app):
    with session_for(app.state.engine) as db:
        rows = db.scalars(
            select(Outbox)
            .where(Outbox.sent_at.is_(None), Outbox.not_before <= app.state.clock())
            .order_by(Outbox.not_before)
            .limit(20)
        ).all()
        envelopes = [(row.id, row.job_id, row.workspace_id) for row in rows]
    for envelope_id, job_id, workspace_id in envelopes:
        with session_for(app.state.engine) as db, db.begin():
            db.get(Outbox, envelope_id).sent_at = app.state.clock()
        execute_job(app, job_id, workspace_id)
    return bool(envelopes)


def collection_state(db, workspace_id, country, period, category, time, settings):
    health = db.get(SourceHealth, "tiktok")
    if health and health.suspended:
        return {"coverage_status": "source_unavailable", "reason": health.reason, "collection_id": None}
    bucket = int(time.timestamp() // (2 * 3600))
    from .feed import normalize

    category_key = sha256(normalize(category or "").encode()).hexdigest()
    key = f"collect:{country}:{category_key}:{bucket}"
    job = enqueue(
        db, workspace_id, "collect", key, {"country": country, "period": period, "category": category}, time
    )
    if job.state == "failed":
        return {"coverage_status": "source_unavailable", "reason": job.error, "collection_id": job.id}
    if job.state == "completed":
        classification = db.scalar(select(Job).where(Job.key == f"classify:{job.id}"))
        if classification and classification.state in {"queued", "running"}:
            return {
                "coverage_status": "collecting",
                "reason": "Classificando os metadados coletados.",
                "collection_id": job.id,
            }
        return {
            "coverage_status": "no_results",
            "reason": "A coleta terminou sem referências elegíveis suficientes para este recorte.",
            "collection_id": job.id,
        }
    return {"coverage_status": "collecting", "reason": job.error, "collection_id": job.id}
