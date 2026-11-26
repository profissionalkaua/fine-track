from datetime import timedelta
from hashlib import sha256
from secrets import compare_digest, token_urlsafe
from typing import Annotated

import pycountry
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pwdlib import PasswordHash
from pydantic import BaseModel, Field
from sqlalchemy import case, select, text
from sqlalchemy.dialects.postgresql import insert

from .db import now, session_for
from .models import LoginAttempt, LoginSession, Membership, User, Workspace

router = APIRouter(prefix="/v1")
passwords = PasswordHash.recommended()
dummy_hash = passwords.hash("dummy-comparison-password")


def digest(value: str):
    return sha256(value.encode()).hexdigest()


def database(request: Request):
    with session_for(request.app.state.engine) as db:
        yield db
        db.commit()


def identity(request: Request, db=Depends(database, scope="function")):
    token = request.cookies.get("pulso_session", "")
    session = db.get(LoginSession, digest(token)) if token else None
    if session is None or session.expires_at <= now():
        raise HTTPException(401, "Entre para acessar seu workspace.")
    membership = db.get(Membership, (session.user_id, session.workspace_id))
    if membership is None:
        raise HTTPException(403, "Você não participa deste workspace.")
    expected_workspace = request.headers.get("x-workspace-id")
    if expected_workspace and expected_workspace != session.workspace_id:
        raise HTTPException(409, "O workspace ativo mudou. Recarregue a área antes de continuar.")
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        if not compare_digest(request.headers.get("x-csrf-token", ""), session.csrf):
            raise HTTPException(403, "Sessão de formulário inválida. Atualize a página.")
        origin = request.headers.get("origin")
        if origin and origin != request.app.state.settings.origin:
            raise HTTPException(403, "Origem inválida.")
    db.execute(text("SELECT set_config('pulso.workspace_id', :id, true)"), {"id": session.workspace_id})
    return session, membership


Identity = Annotated[tuple[LoginSession, Membership], Depends(identity)]


def require_editor(auth):
    if auth[1].role not in {"owner", "editor"}:
        raise HTTPException(403, "Seu papel permite apenas leitura.")


def describe(db, session, membership):
    user = db.get(User, session.user_id)
    workspace = db.get(Workspace, session.workspace_id)
    return {
        "user": {"id": user.id, "email": user.email, "country": user.country},
        "workspace": {"id": workspace.id, "name": workspace.name, "role": membership.role},
        "csrf_token": session.csrf,
    }


class Login(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(min_length=1, max_length=1024)


@router.post("/auth/login")
def login(body: Login, request: Request, response: Response, db=Depends(database, scope="function")):
    if request.headers.get("origin") not in {None, request.app.state.settings.origin}:
        raise HTTPException(403, "Origem inválida.")
    ip = request.client.host if request.client else "unknown"
    time = now()
    for key, limit in [(digest(ip + ":" + body.email.strip().lower()), 10), (digest("ip:" + ip), 100)]:
        statement = insert(LoginAttempt).values(key=key, attempts=1, window_start=time)
        expired = LoginAttempt.window_start < time - timedelta(minutes=5)
        attempts = db.execute(
            statement.on_conflict_do_update(
                index_elements=["key"],
                set_={
                    "attempts": case((expired, 1), else_=LoginAttempt.attempts + 1),
                    "window_start": case((expired, time), else_=LoginAttempt.window_start),
                },
            ).returning(LoginAttempt.attempts)
        ).scalar_one()
        if attempts > limit:
            db.commit()
            raise HTTPException(
                429,
                "Muitas tentativas. Aguarde cinco minutos antes de tentar novamente.",
                headers={"Retry-After": "300"},
            )
    user = db.scalar(select(User).where(User.email == body.email.strip().lower()))
    valid = passwords.verify(body.password, user.password_hash if user else dummy_hash)
    if not valid or user is None:
        db.commit()
        raise HTTPException(401, "Email ou senha inválidos.")
    membership = db.scalar(
        select(Membership).where(Membership.user_id == user.id).order_by(Membership.workspace_id)
    )
    if membership is None:
        raise HTTPException(403, "Nenhum workspace disponível.")
    token = token_urlsafe(32)
    session = LoginSession(
        token_hash=digest(token),
        user_id=user.id,
        workspace_id=membership.workspace_id,
        csrf=token_urlsafe(32),
        expires_at=now() + timedelta(hours=request.app.state.settings.session_hours),
    )
    db.add(session)
    response.set_cookie(
        "pulso_session",
        token,
        httponly=True,
        samesite="lax",
        secure=request.app.state.settings.cookie_secure,
        max_age=request.app.state.settings.session_hours * 3600,
        path="/",
    )
    return describe(db, session, membership)


@router.get("/auth/me")
def me(auth: Identity, db=Depends(database, scope="function")):
    return describe(db, *auth)


@router.post("/auth/logout")
def logout(auth: Identity, response: Response, db=Depends(database, scope="function")):
    db.delete(auth[0])
    response.delete_cookie("pulso_session", path="/")
    return {"ok": True}


class Preference(BaseModel):
    country: str = Field(min_length=2, max_length=2)


@router.patch("/preferences")
def preferences(body: Preference, auth: Identity, db=Depends(database, scope="function")):
    if not pycountry.countries.get(alpha_2=body.country):
        raise HTTPException(422, "País inválido.")
    db.get(User, auth[0].user_id).country = body.country
    return {"country": body.country}


@router.get("/workspaces")
def workspaces(auth: Identity, db=Depends(database, scope="function")):
    rows = db.execute(
        select(Workspace, Membership.role)
        .join(Membership, Membership.workspace_id == Workspace.id)
        .where(Membership.user_id == auth[0].user_id)
        .order_by(Workspace.name)
    ).all()
    return {"items": [{"id": workspace.id, "name": workspace.name, "role": role} for workspace, role in rows]}


class WorkspaceChoice(BaseModel):
    workspace_id: str = Field(max_length=36)


@router.post("/auth/workspace")
def choose_workspace(body: WorkspaceChoice, auth: Identity, db=Depends(database, scope="function")):
    membership = db.get(Membership, (auth[0].user_id, body.workspace_id))
    if membership is None:
        raise HTTPException(403, "Você não participa deste workspace.")
    auth[0].workspace_id = body.workspace_id
    auth[0].csrf = token_urlsafe(32)
    return describe(db, auth[0], membership)
