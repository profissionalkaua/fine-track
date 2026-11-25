import base64
import json
import unicodedata
from datetime import timedelta

from fastapi import HTTPException
from sqlalchemy import select

from .db import now
from .models import Ranking, Snapshot, Video

HOURS = {'day': 24, 'week': 168, 'month': 720}


def normalize(value: str):
    text = unicodedata.normalize('NFKD', value.strip().casefold())
    return ' '.join(''.join(c for c in text if not unicodedata.combining(c)).split())


def category_matches(video: Video, category: str):
    return not category or any(normalize(c['text']) == normalize(category)
                               and (c.get('reviewed') or c.get('confidence', 0) >= .8)
                               for c in video.categories)


def video_data(video, snapshot):
    return {'id': video.id, 'creator_id': video.creator_id, 'handle': video.handle,
            'description': video.description, 'url': video.url, 'thumbnail': video.thumbnail,
            'published_at': video.published_at.isoformat(), 'country': video.country,
            'geo_evidence': video.geo_evidence, 'categories': video.categories,
            'hashtags': [{'key': normalize(t.lstrip('#')), 'label': t.lstrip('#')} for t in video.hashtags],
            'duration': video.duration, 'synthetic': video.synthetic,
            'views': snapshot.views, 'likes': snapshot.likes, 'comments': snapshot.comments,
            'shares': snapshot.shares, 'observed_at': snapshot.observed_at.isoformat()}


def publish_ranking(db, country: str, period: str, category='', as_of=None, freshness=2):
    as_of = as_of or now()
    start = as_of - timedelta(hours=HOURS[period])
    items, most_viewed = [], []
    videos = db.scalars(select(Video).where(Video.country == country, Video.available.is_(True))).all()
    for video in videos:
        if not video.geo_evidence.get('kind') in {'observed', 'inferred'} or not category_matches(video, category):
            continue
        samples = db.scalars(select(Snapshot).where(Snapshot.video_id == video.id,
                            Snapshot.observed_at >= max(start, video.published_at),
                            Snapshot.observed_at <= as_of).order_by(Snapshot.observed_at)).all()
        valid = [s for s in samples if s.views is not None and s.views >= 0]
        if not valid:
            continue
        last = valid[-1]
        data = video_data(video, last)
        most_viewed.append(data)
        if len(valid) < 2:
            continue
        first = valid[0]
        # A changed provider is not a comparable pair.
        comparable = all(s.source == first.source for s in valid)
        monotonic = all(a.views <= b.views for a, b in zip(valid, valid[1:]))
        observed_hours = (last.observed_at - first.observed_at).total_seconds() / 3600
        partial = video.published_at > start
        minimum = (2 if period == 'day' else 12) if partial else HOURS[period] * .75
        if not comparable or not monotonic or observed_hours < minimum:
            continue
        if (as_of - last.observed_at).total_seconds() > freshness * 3600:
            continue
        delta = last.views - first.views
        data.update(delta_views=delta, velocity=delta / observed_hours, partial_window=partial,
                    observed_hours=observed_hours, snapshot_ids=[first.id, last.id])
        items.append(data)
    items.sort(key=lambda v: (-v['velocity'], -v['delta_views'],
                              -__import__('datetime').datetime.fromisoformat(v['observed_at']).timestamp(), v['id']))
    for rank, item in enumerate(items, 1):
        item['rank'] = rank
    ranked = {v['id'] for v in items}
    most_viewed = sorted((v for v in most_viewed if v['id'] not in ranked),
                         key=lambda v: (-v['views'], v['id']))[:20]
    ranking = Ranking(country=country, period=period, category=normalize(category), as_of=as_of,
                      items=items, most_viewed=most_viewed)
    db.add(ranking)
    db.flush()
    return ranking


def get_feed(db, country, period, category, limit, cursor, as_of, settings):
    if not 1 <= limit <= 50:
        raise HTTPException(422, 'O limite deve estar entre 1 e 50.')
    offset = 0
    ranking = None
    if cursor:
        try:
            if len(cursor) > 512:
                raise ValueError()
            ref, offset = json.loads(base64.urlsafe_b64decode(cursor))
            if not isinstance(ref, str) or not isinstance(offset, int) or offset < 0:
                raise ValueError()
            ranking = db.get(Ranking, ref)
            if ranking is None or (ranking.country, ranking.period, ranking.category) != (
                    country, period, normalize(category or '')) or as_of - ranking.as_of > timedelta(hours=24):
                raise ValueError()
        except (ValueError, TypeError, json.JSONDecodeError):
            raise HTTPException(409, 'Cursor inválido ou expirado. Recarregue a primeira página.')
    else:
        ranking = db.scalar(select(Ranking).where(Ranking.country == country, Ranking.period == period,
                            Ranking.category == normalize(category or '')).order_by(Ranking.as_of.desc()))
    count = len(ranking.items) if ranking else 0
    next_offset = offset + limit
    next_cursor = base64.urlsafe_b64encode(json.dumps([ranking.id, next_offset]).encode()).decode() if (
        ranking and next_offset < count) else None
    coverage = 'ready' if count >= 20 else ('partial_coverage' if count else 'no_results')
    if ranking is None:
        coverage = 'collecting' if settings.collection_enabled else 'source_unavailable'
    return {'items': ranking.items[offset:next_offset] if ranking else [], 'country': country,
            'period': period, 'category': category or None, 'coverage_status': coverage,
            'eligible_count': count, 'as_of': ranking.as_of if ranking else None,
            'version': ranking.id if ranking else None, 'algorithm': 'velocity-v1', 'cursor': next_cursor,
            'window_start': (ranking.as_of if ranking else as_of) - timedelta(hours=HOURS[period]),
            'window_end': ranking.as_of if ranking else as_of,
            'most_viewed': ranking.most_viewed if ranking else [],
            'is_stale': bool(ranking and as_of - ranking.as_of > timedelta(hours=settings.latest_snapshot_hours)),
            'reason': 'A fonte ainda não foi configurada para este ambiente.' if ranking is None and
                      not settings.collection_enabled else None}
