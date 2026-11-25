from collections import defaultdict

from sqlalchemy import select

from .db import session_for
from .feed import publish_ranking
from .models import Video


def classify_job(app, payload):
    with session_for(app.state.engine) as db:
        videos = db.scalars(select(Video).where(Video.id.in_(payload["video_ids"]))).all()
        references = [{"id": v.id, "description": v.description, "hashtags": v.hashtags} for v in videos]
    labels = app.state.classifier.classify(references, payload.get("category"))
    grouped = defaultdict(list)
    for label in labels:
        grouped[label["video_id"]].append({k: v for k, v in label.items() if k != "video_id"})
    with session_for(app.state.engine) as db, db.begin():
        for video_id, assignments in grouped.items():
            video = db.get(Video, video_id)
            if video:
                reviewed = [
                    label
                    for label in video.categories
                    if label.get("reviewed") or label.get("confidence", 0) >= 0.8
                ]
                video.categories = [*reviewed, *assignments]
        db.flush()
        for period in ["day", "week", "month"]:
            publish_ranking(
                db,
                payload["country"],
                period,
                payload.get("category") or "",
                as_of=app.state.clock(),
                freshness=app.state.settings.latest_snapshot_hours,
            )
