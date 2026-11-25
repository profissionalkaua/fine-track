from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from .auth import Identity, database, require_editor
from .feed import normalize, publish_ranking
from .models import BrandVersion, User, Workspace

router = APIRouter(prefix="/v1/brand-rules")
ELEMENTS = {"hook", "structure", "cta", "pace", "on_screen_text", "duration", "retention"}
DEFAULTS = {
    "target_audience": "",
    "tone": "",
    "guidelines": "",
    "preferred_format": "",
    "analysis_elements": ["hook", "structure", "cta"],
}


def current_rules(db):
    return db.scalar(select(BrandVersion).order_by(BrandVersion.version.desc()).limit(1))


def describe(version):
    return {
        "version": version.version if version else 0,
        "category_text": version.category_text if version else None,
        **(version.content if version else DEFAULTS),
        "saved_at": version.created_at.isoformat() if version else None,
    }


class BrandPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_version: int = Field(ge=0)
    category_text: str | None = Field(default=None, max_length=250)
    target_audience: str = Field(default="", max_length=4000)
    tone: str = Field(default="", max_length=2000)
    guidelines: str = Field(default="", max_length=8000)
    preferred_format: str = Field(default="", max_length=1000)
    analysis_elements: list[str] = Field(default_factory=list, max_length=7)


@router.get("")
def get_rules(auth: Identity, db=Depends(database, scope="function")):
    return describe(current_rules(db))


@router.patch("")
def save_rules(body: BrandPatch, auth: Identity, request: Request, db=Depends(database, scope="function")):
    require_editor(auth)
    if not set(body.analysis_elements) <= ELEMENTS:
        raise HTTPException(422, "Elemento de análise inválido.")
    db.execute(select(Workspace).where(Workspace.id == auth[0].workspace_id).with_for_update())
    previous = current_rules(db)
    if body.expected_version != (previous.version if previous else 0):
        raise HTTPException(409, "As regras foram alteradas. Recarregue a versão salva antes de editar.")
    patch = body.model_dump(exclude_unset=True, exclude={"expected_version"})
    category = previous.category_text if previous else None
    if "category_text" in patch:
        category = (patch.pop("category_text") or "").strip() or None
    content = {**(previous.content if previous else DEFAULTS), **patch}
    version = BrandVersion(
        workspace_id=auth[0].workspace_id,
        version=body.expected_version + 1,
        category_text=category,
        category_key=normalize(category or ""),
        content=content,
        author_id=auth[0].user_id,
        created_at=request.app.state.clock(),
    )
    db.add(version)
    country = db.get(User, auth[0].user_id).country
    for period in ["day", "week", "month"]:
        publish_ranking(
            db,
            country,
            period,
            category or "",
            as_of=request.app.state.clock(),
            freshness=request.app.state.settings.latest_snapshot_hours,
        )
    db.flush()
    return describe(version)
