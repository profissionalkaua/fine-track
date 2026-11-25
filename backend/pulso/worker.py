"""Celery workers and an explicit single-process development executor."""

import sys
import time

from celery import Celery
from sqlalchemy import select

from .config import Settings
from .db import now, session_for
from .jobs import drain_once, execute_job
from .models import Outbox

settings = Settings()
celery = Celery("pulso", broker=settings.broker_url)
celery.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_serializer="json",
    # Do not mark an outbox envelope sent until RabbitMQ confirms persistence.
    broker_transport_options={"confirm_publish": True},
    task_default_delivery_mode="persistent",
    accept_content=["json"],
    result_serializer="json",
    broker_connection_retry_on_startup=True,
    task_soft_time_limit=540,
    task_time_limit=600,
    timezone="UTC",
    beat_schedule={
        "outbox": {"task": "pulso.dispatch", "schedule": 5.0},
        "schedule": {"task": "pulso.schedule", "schedule": 300.0},
        "retention": {"task": "pulso.retain", "schedule": 86400.0},
    },
)


def application():
    from .main import create_app

    return create_app(settings)


@celery.task(name="pulso.execute")
def execute(job_id, workspace_id):
    app = application()
    try:
        execute_job(app, job_id, workspace_id)
    finally:
        app.state.engine.dispose()


@celery.task(name="pulso.dispatch")
def dispatch():
    app = application()
    try:
        with session_for(app.state.engine) as db, db.begin():
            envelopes = db.scalars(
                select(Outbox)
                .where(Outbox.sent_at.is_(None), Outbox.not_before <= now())
                .with_for_update(skip_locked=True)
                .limit(20)
            ).all()
            for envelope in envelopes:
                execute.apply_async(args=[envelope.job_id, envelope.workspace_id], queue=envelope.queue)
                envelope.sent_at = now()
    finally:
        app.state.engine.dispose()


@celery.task(name="pulso.schedule")
def schedule():
    from .scheduler import schedule_once

    app = application()
    try:
        schedule_once(app)
    finally:
        app.state.engine.dispose()


@celery.task(name="pulso.retain")
def retention():
    from .scheduler import retain

    app = application()
    try:
        retain(app)
    finally:
        app.state.engine.dispose()


if __name__ == "__main__":
    if sys.argv[1:] != ["local"] or settings.environment != "development":
        raise SystemExit("Use Celery em produção. Para desenvolvimento: python -m pulso.worker local")
    app = application()
    print("Worker local ativo. Ctrl+C para encerrar.", flush=True)
    try:
        from .scheduler import retain, schedule_once

        schedule_once(app)
        retain(app)
        last_schedule = time.monotonic()
        while True:
            drain_once(app)
            if time.monotonic() - last_schedule > 300:
                schedule_once(app)
                last_schedule = time.monotonic()
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        app.state.engine.dispose()
