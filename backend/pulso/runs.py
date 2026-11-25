import json
from hashlib import sha256
from typing import Annotated, Literal

import pycountry
from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from .auth import Identity, database, require_editor
from .brands import current_rules
from .brands import describe as describe_rules
from .db import session_for, uid
from .feed import category_matches, get_feed, video_data
from .jobs import enqueue, workspace
from .models import AuthorizedMedia, Creator, Run, Snapshot, Video, WorkspaceCreator

router = APIRouter(prefix="/v1/runs")
Key = Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=128)]


class RunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scope: Literal["feed", "video"] = "feed"
    country: str = Field(default="BR", min_length=2, max_length=2)
    period: Literal["day", "week", "month"] = "day"
    hashtag: str | None = Field(default=None, max_length=100)
    video_id: str | None = Field(default=None, max_length=32)
    video_ids: list[str] | None = Field(default=None, max_length=20)
    creator_ids: list[str] | None = Field(default=None, max_length=30)
    rules_version: int | None = Field(default=None, ge=0)
    ranking_version: str | None = Field(default=None, max_length=36)


def describe(run):
    return {
        "id": run.id,
        "scope": run.scope,
        "state": run.state,
        "progress": run.progress,
        "processed": run.processed,
        "frozen": run.frozen,
        "result": run.result,
        "errors": run.errors,
        "created_at": run.created_at,
        "updated_at": run.updated_at,
        "parent_id": run.parent_id,
    }


def find(db, run_id):
    run = db.get(Run, run_id)
    if run is None:
        raise HTTPException(404, "Execução não encontrada neste workspace.")
    return run


def snapshot_video(db, video):
    sample = db.scalar(
        select(Snapshot).where(Snapshot.video_id == video.id).order_by(Snapshot.observed_at.desc())
    )
    return video_data(video, sample) if sample else None


def freeze(db, body, auth, app):
    if not pycountry.countries.get(alpha_2=body.country):
        raise HTTPException(422, "País inválido.")
    rules = current_rules(db)
    revision = rules.version if rules else 0
    if body.rules_version is not None and body.rules_version != revision:
        raise HTTPException(409, "As regras mudaram. Atualize a configuração antes de analisar.")
    category = rules.category_text if rules else None
    refs: dict[str, dict] = {}
    groups = []
    ranking_version = None
    if body.scope == "video":
        if not body.video_id:
            raise HTTPException(422, "A análise individual exige um vídeo.")
        video = db.get(Video, body.video_id)
        if video is None or not video.available:
            raise HTTPException(404, "Vídeo indisponível.")
        item = snapshot_video(db, video)
        if item:
            refs[item["id"]] = {**item, "origins": ["top_video"]}
    else:
        feed = get_feed(
            db, body.country, body.period, category, 50, None, app.state.clock(), app.state.settings
        )
        ranking_version = feed["version"]
        if body.ranking_version and body.ranking_version != ranking_version:
            from .models import Ranking

            ranking = db.get(Ranking, body.ranking_version)
            from .feed import normalize

            if not ranking or (ranking.country, ranking.period, ranking.category) != (
                body.country,
                body.period,
                normalize(category or ""),
            ):
                raise HTTPException(409, "O ranking não corresponde ao recorte. Atualize o feed.")
            feed["items"], ranking_version = ranking.items, ranking.id
        items = feed["items"]
        if ranking_version:
            from .models import Ranking

            full_ranking = db.get(Ranking, ranking_version)
            items = full_ranking.items
        if body.video_ids is not None:
            requested = set(body.video_ids)
            if not requested <= {v["id"] for v in items}:
                raise HTTPException(409, "Uma referência saiu do ranking selecionado. Atualize o feed.")
            items = [v for v in items if v["id"] in requested]
        if body.hashtag:
            items = [v for v in items if any(tag["key"] == body.hashtag for tag in v["hashtags"])]
        for item in items[:20]:
            refs[item["id"]] = {**item, "origins": ["top_video"]}
        saved = db.scalars(
            select(WorkspaceCreator)
            .where(WorkspaceCreator.status == "active")
            .order_by(WorkspaceCreator.created_at)
        ).all()
        if body.creator_ids is not None:
            if not set(body.creator_ids) <= {ref.id for ref in saved}:
                raise HTTPException(422, "Selecione somente perfis salvos e ativos.")
            saved = [ref for ref in saved if ref.id in body.creator_ids]
        total = 0
        for ref in saved:
            group = {"creator_id": ref.creator_id, "handle": ref.handle, "references": [], "warnings": []}
            creator = db.get(Creator, ref.creator_id)
            if not creator or not creator.available:
                group["warnings"].append("Criador indisponível.")
                groups.append(group)
                continue
            videos = (
                db.scalars(
                    select(Video)
                    .where(Video.creator_id == ref.creator_id, Video.available.is_(True))
                    .order_by(Video.published_at.desc())
                    .limit(min(5, 30 - total))
                ).all()
                if total < 30
                else []
            )
            for video in videos:
                item = snapshot_video(db, video)
                if not item:
                    continue
                total += 1
                group["references"].append(item["id"])
                if not category_matches(video, category or ""):
                    group["warnings"].append(f"{item['id']}: fora da categoria, excluído do resumo temático.")
                    continue
                if item["id"] in refs:
                    refs[item["id"]]["origins"].append("competitor")
                else:
                    refs[item["id"]] = {**item, "origins": ["competitor"]}
            groups.append(group)
    return {
        "country": body.country,
        "period": body.period,
        "category": category,
        "hashtag": body.hashtag,
        "rules_version": revision,
        "rules": describe_rules(rules),
        "ranking_version": ranking_version,
        "references": list(refs.values()),
        "creator_groups": groups,
        "request": body.model_dump(),
        "captured_at": app.state.clock().isoformat(),
        "budget": {"feed": 20, "creators": 30},
    }


def create(db, body, auth, app, key, parent_id=None):
    require_editor(auth)
    fingerprint = sha256(
        json.dumps({"request": body.model_dump(), "parent_id": parent_id}, sort_keys=True).encode()
    ).hexdigest()
    previous = db.scalar(select(Run).where(Run.idempotency_key == key))
    if previous:
        if previous.request_hash != fingerprint:
            raise HTTPException(409, "Esta chave de idempotência já foi usada com outra entrada.")
        return previous
    frozen = freeze(db, body, auth, app)
    run_id = uid()
    db.execute(
        insert(Run)
        .values(
            id=run_id,
            workspace_id=auth[0].workspace_id,
            idempotency_key=key,
            request_hash=fingerprint,
            parent_id=parent_id,
            scope=body.scope,
            state="queued",
            progress=0,
            processed=0,
            frozen=frozen,
            errors=[],
            created_at=app.state.clock(),
            updated_at=app.state.clock(),
        )
        .on_conflict_do_nothing(index_elements=["workspace_id", "idempotency_key"])
    )
    run = db.scalar(select(Run).where(Run.idempotency_key == key))
    if run.request_hash != fingerprint:
        raise HTTPException(409, "Esta chave de idempotência já foi usada com outra entrada.")
    media_required = bool(
        db.scalar(
            select(AuthorizedMedia.video_id)
            .where(AuthorizedMedia.video_id.in_([r["id"] for r in frozen["references"]]))
            .limit(1)
        )
    )
    enqueue(
        db,
        auth[0].workspace_id,
        "run",
        f"run:{run.id}",
        {"run_id": run.id, "media_required": media_required},
        app.state.clock(),
    )
    return run


@router.post("", status_code=202)
def create_run(
    body: RunRequest, auth: Identity, request: Request, idempotency_key: Key, db=Depends(database)
):
    return describe(create(db, body, auth, request.app, idempotency_key))


@router.get("")
def list_runs(auth: Identity, db=Depends(database)):
    runs = db.scalars(select(Run).order_by(Run.created_at.desc()).limit(20)).all()
    return {"items": [describe(run) for run in runs]}


@router.post("/preview")
def preview(body: RunRequest, auth: Identity, request: Request, db=Depends(database)):
    frozen = freeze(db, body, auth, request.app)
    return {
        "eligible_count": len(frozen["references"]),
        "frozen": frozen,
        "model_configured": bool(request.app.state.settings.ollama_model),
        "collection_enabled": request.app.state.settings.collection_enabled,
    }


@router.get("/{run_id}")
def get_run(run_id: str, auth: Identity, db=Depends(database)):
    return describe(find(db, run_id))


@router.get("/{run_id}/export")
def export_run(run_id: str, auth: Identity, db=Depends(database)):
    run = find(db, run_id)
    content = {"schema_version": "1.0", **describe(run)}
    return Response(
        json.dumps(content, ensure_ascii=False, default=str),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="pulso-{run.id}.json"'},
    )


@router.post("/{run_id}/cancel")
def cancel_run(run_id: str, auth: Identity, request: Request, db=Depends(database)):
    require_editor(auth)
    run = db.scalar(select(Run).where(Run.id == run_id).with_for_update())
    if run is None:
        raise HTTPException(404, "Execução não encontrada neste workspace.")
    if run.state not in {"completed", "failed", "partial", "cancelled"}:
        run.state, run.updated_at = "cancelled", request.app.state.clock()
    return describe(run)


@router.post("/{run_id}/resume", status_code=202)
def resume_run(
    run_id: str,
    auth: Identity,
    request: Request,
    idempotency_key: Key,
    body: RunRequest | None = None,
    db=Depends(database),
):
    run = find(db, run_id)
    if run.state not in {"partial", "failed", "cancelled"}:
        raise HTTPException(409, "Aguarde a conclusão ou cancele antes de retomar.")
    if body is None:
        previous = dict(run.frozen["request"])
        for field in ["video_ids", "ranking_version", "rules_version"]:
            previous.pop(field, None)
        body = RunRequest.model_validate(previous)
    return describe(create(db, body, auth, request.app, idempotency_key, parent_id=run.id))


def transition(app, run_id, workspace_id, state, progress, **updates):
    with session_for(app.state.engine) as db, db.begin():
        workspace(db, workspace_id)
        run = db.scalar(select(Run).where(Run.id == run_id).with_for_update())
        if run is None or run.state in {"cancelled", "completed", "partial", "failed"}:
            return False
        run.state, run.progress, run.updated_at = state, progress, app.state.clock()
        for key, value in updates.items():
            setattr(run, key, value)
        return True


def signal_availability(prepared):
    signals = {
        ref["id"]: {
            "retention_analytics": False,
            "audio": ref.get("analise_visual", {}).get("transcription", {}).get("state") == "completed",
            "visual_frames": bool(ref.get("analise_visual", {}).get("frames")),
        }
        for ref in prepared
    }
    return {
        "signal_availability": signals,
        "unavailable_signals": [
            name for name in ("retention_analytics", "audio", "visual_frames")
            if not signals or any(not available[name] for available in signals.values())
        ],
    }


def execute_run(app, run_id, workspace_id):

    if not transition(app, run_id, workspace_id, "collecting", 10):
        return
    with session_for(app.state.engine) as db:
        workspace(db, workspace_id)
        run = db.get(Run, run_id)
        frozen, scope = run.frozen, run.scope
    refs = frozen["references"]
    minimum = 1 if scope == "video" else 5
    visual = {
        "state": "unavailable",
        "reason": "Mídia autorizada não disponível para esta análise.",
        "segments": [],
    }
    if len(refs) < minimum:
        transition(
            app,
            run_id,
            workspace_id,
            "partial",
            100,
            processed=len(refs),
            errors=[
                {
                    "stage": "collecting",
                    "code": "insufficient_references",
                    "message": f"Amostra insuficiente: {len(refs)} de {minimum} referências elegíveis. Aguarde a coleta e retome.",
                }
            ],
            result={"ideas": [], "evidence": [], "analise_visual": visual, **signal_availability(refs)},
        )
        return
    if not transition(app, run_id, workspace_id, "analyzing", 35):
        return
    evidence = []
    prepared = []
    for ref in refs:
        signals = [
            {
                "video_id": ref["id"],
                "source": "description",
                "kind": "observed",
                "observation": ref["description"],
                "confidence": 1,
                "timestamp_ms": None,
            },
            {
                "video_id": ref["id"],
                "source": "metrics",
                "kind": "observed",
                "observation": f"Views públicas: {ref.get('views')}; observação: {ref['observed_at']}",
                "confidence": 1,
                "timestamp_ms": None,
            },
        ]
        evidence.extend(signals)
        from .media import analyze_authorized

        media = analyze_authorized(app, workspace_id, ref)
        if scope == "video":
            visual = media
        transcript = " ".join(s["text"] for s in media.get("transcription", {}).get("segments", []))
        prepared.append({**ref, "evidence": signals, "analise_visual": media, "transcript": transcript})
    if not transition(app, run_id, workspace_id, "generating", 65, processed=len(prepared)):
        return
    with session_for(app.state.engine) as db, db.begin():
        workspace(db, workspace_id)
        run = db.scalar(select(Run).where(Run.id == run_id).with_for_update())
        if run.state == "cancelled":
            return
        if any(reference["analise_visual"].get("state") != "unavailable" for reference in prepared):
            run.result = {
                "ideas": [],
                "evidence": evidence,
                "analise_visual": visual,
                "visual_analyses": {reference["id"]: reference["analise_visual"] for reference in prepared},
                **signal_availability(prepared),
            }
        enqueue(
            db,
            workspace_id,
            "generate",
            f"generate:{run_id}",
            {"run_id": run_id, "scope": scope, "prepared": prepared, "visual": visual, "evidence": evidence},
            app.state.clock(),
        )


def generate_run(app, payload, workspace_id):
    from .adapters.ollama import ModelError, validate_ideas

    run_id = payload["run_id"]
    with session_for(app.state.engine) as db:
        workspace(db, workspace_id)
        run = db.get(Run, run_id)
        if run is None or run.state in {"cancelled", "completed", "partial", "failed"}:
            return
        frozen, scope = run.frozen, run.scope
    prepared, visual, evidence = payload["prepared"], payload["visual"], payload["evidence"]
    count = 1 if scope == "video" else 5
    try:
        result = validate_ideas(
            app.state.generator.generate(prepared, frozen["rules"], count), prepared, count
        )
    except (ModelError, ValueError) as exc:
        transition(
            app,
            run_id,
            workspace_id,
            "failed",
            100,
            errors=[{"stage": "generating", "code": "model_unavailable_or_invalid", "message": str(exc)}],
        )
        return
    result.update(
        evidence=evidence,
        analise_visual=visual,
        visual_analyses={ref["id"]: ref["analise_visual"] for ref in prepared},
        model_version=app.state.generator.model_version,
        **signal_availability(prepared),
        methodology="Associações observadas e hipóteses editoriais; sem inferência de causalidade.",
    )
    transition(app, run_id, workspace_id, "completed", 100, result=result, processed=len(prepared))
