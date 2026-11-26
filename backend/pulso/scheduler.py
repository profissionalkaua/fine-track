"""One scheduler schedules public observations; workspace rules remain scoped by RLS."""

import shutil
from datetime import timedelta
from pathlib import Path

from sqlalchemy import delete, select

from .brands import current_rules
from .db import session_for
from .jobs import enqueue, workspace
from .models import (
    CollectionCache,
    LoginAttempt,
    LoginSession,
    Membership,
    Ranking,
    Run,
    Snapshot,
    SourceObservation,
    User,
    VideoAnalysis,
    Workspace,
    WorkspaceCreator,
)


def schedule_once(app):
    if not app.state.settings.collection_enabled:
        return
    time = app.state.clock()
    with session_for(app.state.engine) as db, db.begin():
        for item in db.scalars(select(Workspace)).all():
            workspace(db, item.id)
            rules = current_rules(db)
            category = rules.category_text if rules else None
            countries = set(
                db.scalars(
                    select(User.country)
                    .join(Membership, Membership.user_id == User.id)
                    .where(Membership.workspace_id == item.id)
                ).all()
            )
            handles = db.scalars(
                select(WorkspaceCreator.handle)
                .where(WorkspaceCreator.status == "active")
                .order_by(WorkspaceCreator.handle)
            ).all()
            for country in countries:
                for mode, hours in [("trending", 2), ("hashtags", 4), ("creators", 6)]:
                    if mode == "creators" and not handles:
                        continue
                    bucket = int(time.timestamp() // (hours * 3600))
                    batches = (
                        [list(handles)[start : start + 6] for start in range(0, len(handles), 6)]
                        if mode == "creators"
                        else [[]]
                    )
                    for batch_index, batch in enumerate(batches):
                        enqueue(
                            db,
                            item.id,
                            "collect",
                            f"schedule:{mode}:{country}:{bucket}:{batch_index}",
                            {
                                "country": country,
                                "period": "day",
                                "category": category,
                                "mode": mode,
                                "handles": batch,
                            },
                            time,
                        )


def retain(app):
    time = app.state.clock()
    with session_for(app.state.engine) as db, db.begin():
        db.execute(delete(Snapshot).where(Snapshot.observed_at < time - timedelta(days=35)))
        db.execute(delete(SourceObservation).where(SourceObservation.observed_at < time - timedelta(days=35)))
        db.execute(delete(Ranking).where(Ranking.as_of < time - timedelta(days=2)))
        db.execute(delete(CollectionCache).where(CollectionCache.expires_at < time))
        db.execute(delete(LoginAttempt).where(LoginAttempt.window_start < time - timedelta(days=1)))
        db.execute(delete(LoginSession).where(LoginSession.expires_at < time))
        for item in db.scalars(select(Workspace)).all():
            workspace(db, item.id)
            cutoff = time - timedelta(days=app.state.settings.retention_days)
            db.execute(
                delete(Run).where(
                    Run.created_at < cutoff, Run.state.in_(["completed", "failed", "partial", "cancelled"])
                )
            )
            db.execute(delete(VideoAnalysis).where(VideoAnalysis.created_at < cutoff))
    root = Path(app.state.settings.media_temp_root).resolve()
    if root.is_dir():
        for directory in root.glob("pulso-media-*"):
            resolved = directory.resolve()
            if (
                directory.is_dir()
                and not directory.is_symlink()
                and resolved.parent == root
                and time.timestamp() - directory.stat().st_mtime > 86400
            ):
                shutil.rmtree(resolved)
