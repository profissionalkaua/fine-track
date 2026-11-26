import base64
import json
from bisect import bisect_left, bisect_right

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from .adapters.tiktok import SourceError, parse_handle
from .auth import Identity, database, require_editor
from .db import session_for, uid
from .feed import HOURS, publish_ranking
from .jobs import enqueue, workspace
from .models import Creator, Ranking, WorkspaceCreator

router = APIRouter(prefix="/v1/creators")


def describe(db, ref):
    creator = db.get(Creator, ref.creator_id) if ref.creator_id else None
    return {
        "id": ref.id,
        "creator_id": ref.creator_id,
        "handle": creator.handle if creator else ref.handle,
        "name": creator.name if creator else ref.handle,
        "status": ref.status,
        "error": ref.error,
        "observed_at": creator.observed_at if creator else None,
    }


def find(db, ref_id):
    ref = db.get(WorkspaceCreator, ref_id)
    if ref is None:
        raise HTTPException(404, "Perfil salvo não encontrado.")
    return ref


class AddProfile(BaseModel):
    input: str = Field(min_length=1, max_length=300)


class Confirmation(BaseModel):
    creator_id: str


@router.get("")
def list_creators(auth: Identity, db=Depends(database, scope="function")):
    refs = db.scalars(
        select(WorkspaceCreator)
        .where(WorkspaceCreator.status != "removed")
        .order_by(WorkspaceCreator.created_at)
    ).all()
    return {"items": [describe(db, ref) for ref in refs]}


@router.post("", status_code=202)
def add_profile(body: AddProfile, auth: Identity, request: Request, db=Depends(database, scope="function")):
    require_editor(auth)
    try:
        handle = parse_handle(body.input)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from None
    ref_id = uid()
    db.execute(
        insert(WorkspaceCreator)
        .values(
            id=ref_id,
            workspace_id=auth[0].workspace_id,
            handle=handle,
            status="pending",
            created_at=request.app.state.clock(),
        )
        .on_conflict_do_nothing(index_elements=["workspace_id", "handle"])
    )
    ref = db.scalar(select(WorkspaceCreator).where(WorkspaceCreator.handle == handle))
    if ref.status == "pending":
        enqueue(
            db,
            auth[0].workspace_id,
            "profile",
            f"profile:{ref.id}",
            {"reference_id": ref.id, "handle": handle},
            request.app.state.clock(),
        )
    return describe(db, ref)


@router.post("/{ref_id}/confirm")
def confirm(ref_id: str, body: Confirmation, auth: Identity, request: Request, db=Depends(database, scope="function")):
    require_editor(auth)
    ref = find(db, ref_id)
    if ref.status not in {"preview", "active"} or ref.creator_id != body.creator_id:
        raise HTTPException(409, "O perfil mudou ou ainda não foi confirmado pela fonte. Atualize a prévia.")
    ref.status = "active"
    if request.app.state.settings.collection_enabled:
        enqueue(
            db,
            auth[0].workspace_id,
            "collect",
            f"creator:{ref.creator_id}:{int(request.app.state.clock().timestamp() // 21600)}",
            {"country": "BR", "period": "day", "handles": [ref.handle]},
            request.app.state.clock(),
        )
    return describe(db, ref)


@router.delete("/{ref_id}")
def remove(ref_id: str, auth: Identity, db=Depends(database, scope="function")):
    require_editor(auth)
    ref = find(db, ref_id)
    if ref.status != "removed":
        ref.previous_status, ref.status = ref.status, "removed"
    return {"ok": True, "id": ref.id}


@router.post("/{ref_id}/restore")
def restore(ref_id: str, auth: Identity, db=Depends(database, scope="function")):
    require_editor(auth)
    ref = find(db, ref_id)
    if ref.status == "removed":
        ref.status = ref.previous_status or "pending"
    return describe(db, ref)


@router.post("/{ref_id}/retry", status_code=202)
def retry(ref_id: str, auth: Identity, request: Request, db=Depends(database, scope="function")):
    require_editor(auth)
    ref = find(db, ref_id)
    if ref.status == "removed":
        raise HTTPException(409, "Restaure o perfil antes de tentar novamente.")
    ref.status, ref.error = "pending", None
    enqueue(
        db,
        auth[0].workspace_id,
        "profile",
        f"profile:{ref.id}:{uid()}",
        {"reference_id": ref.id, "handle": ref.handle},
        request.app.state.clock(),
    )
    return describe(db, ref)


@router.get("/{ref_id}/videos")
def videos(
    ref_id: str,
    auth: Identity,
    request: Request,
    order: str = "recent",
    period: str = "day",
    cursor: str | None = None,
    db=Depends(database, scope="function"),
):
    ref = find(db, ref_id)
    if ref.status != "active":
        return {
            "items": [],
            "cursor": None,
            "status": ref.status,
            "reason": "Confirme o perfil para ver os vídeos.",
        }
    if order not in {"recent", "performance", "views"} or period not in HOURS:
        raise HTTPException(422, "Ordenação ou período inválido.")
    offset = 0
    ranking = None
    if cursor:
        try:
            ranking_id, saved_ref, saved_order, saved_period, offset = json.loads(
                base64.urlsafe_b64decode(cursor)
            )
            ranking = db.get(Ranking, ranking_id)
            if (
                (saved_ref, saved_order, saved_period) != (ref_id, order, period)
                or not isinstance(offset, int)
                or offset < 0
                or not ranking
                or ranking.category != f"creator:{ref.creator_id}"
            ):
                raise ValueError()
        except (ValueError, TypeError):
            raise HTTPException(409, "Cursor inválido. Recarregue a lista do perfil.") from None
    else:
        ranking = publish_ranking(
            db,
            "*",
            period,
            as_of=request.app.state.clock(),
            freshness=request.app.state.settings.latest_snapshot_hours,
            creator_id=ref.creator_id,
        )
    items = ranking.items + ranking.most_viewed
    # Compare growth over the same period and window coverage, never lifetime views.
    for item in items:
        cohort = sorted(
            other["velocity"]
            for other in ranking.items
            if other["partial_window"] == item.get("partial_window")
            and abs(other["observed_hours"] - item.get("observed_hours", 0)) <= 1
        )
        item["comparable_posts"] = len(cohort)
        item["relative_percentile"] = None
        if len(cohort) >= 10 and item.get("velocity") is not None:
            low = bisect_left(cohort, item["velocity"])
            high = bisect_right(cohort, item["velocity"])
            item["relative_percentile"] = round(100 * (low + (high - low) / 2) / len(cohort), 1)
    if order == "performance":
        items = sorted((v for v in items if v.get("velocity") is not None), key=lambda v: -v["velocity"])
    else:
        items.sort(key=lambda v: v["published_at"] if order == "recent" else v["views"] or -1, reverse=True)
    next_cursor = (
        base64.urlsafe_b64encode(
            json.dumps([ranking.id, ref_id, order, period, offset + 20]).encode()
        ).decode()
        if offset + 20 < len(items)
        else None
    )
    return {
        "items": items[offset : offset + 20],
        "cursor": next_cursor,
        "status": "ready",
        "period": period,
        "as_of": ranking.as_of,
        "reason": None if items else "Ainda não há observações elegíveis para este perfil.",
    }


def resolve_profile(app, payload, workspace_id):
    try:
        from .sources import fetch_shared

        profile = fetch_shared(app, "profile", payload["handle"])
    except SourceError as exc:
        with session_for(app.state.engine) as db, db.begin():
            workspace(db, workspace_id)
            ref = db.get(WorkspaceCreator, payload["reference_id"])
            if ref and ref.status != "removed":
                ref.status, ref.error = "unavailable", str(exc)
        raise
    with session_for(app.state.engine) as db, db.begin():
        workspace(db, workspace_id)
        ref = db.get(WorkspaceCreator, payload["reference_id"])
        if ref is None or ref.status == "removed":
            return
        existing = db.scalar(
            select(WorkspaceCreator).where(
                WorkspaceCreator.creator_id == profile["id"], WorkspaceCreator.id != ref.id
            )
        )
        if existing:
            ref.status, ref.error = "unavailable", "Este criador já tem uma referência salva neste workspace."
            return
        creator = db.get(Creator, profile["id"]) or Creator(id=profile["id"])
        creator.handle, creator.name = profile["handle"], profile["name"]
        creator.available, creator.observed_at = profile["available"], app.state.clock()
        db.add(creator)
        db.flush()
        ref.creator_id = creator.id
        ref.status = "preview" if profile["available"] else "unavailable"
        ref.error = None if profile["available"] else "Perfil privado ou indisponível."
