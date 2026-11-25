from datetime import timedelta
from hashlib import sha256
from secrets import compare_digest, token_urlsafe
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from pwdlib import PasswordHash
from sqlalchemy import select, text
import pycountry

from .db import now, session_for
from .models import LoginSession, Membership, User, Workspace

router = APIRouter(prefix='/v1')
passwords = PasswordHash.recommended()
dummy_hash = passwords.hash('dummy-comparison-password')


def digest(value: str):
    return sha256(value.encode()).hexdigest()


def database(request: Request):
    with session_for(request.app.state.engine) as db:
        yield db
        db.commit()


def identity(request: Request, db=Depends(database)):
    token = request.cookies.get('pulso_session', '')
    session = db.get(LoginSession, digest(token)) if token else None
    if session is None or session.expires_at <= now():
        raise HTTPException(401, 'Entre para acessar seu workspace.')
    membership = db.get(Membership, (session.user_id, session.workspace_id))
    if membership is None:
        raise HTTPException(403, 'Você não participa deste workspace.')
    if request.method not in {'GET', 'HEAD', 'OPTIONS'}:
        if not compare_digest(request.headers.get('x-csrf-token', ''), session.csrf):
            raise HTTPException(403, 'Sessão de formulário inválida. Atualize a página.')
        origin = request.headers.get('origin')
        if origin and origin != request.app.state.settings.origin:
            raise HTTPException(403, 'Origem inválida.')
    db.execute(text("SELECT set_config('pulso.workspace_id', :id, true)"), {'id': session.workspace_id})
    return session, membership


Identity = Annotated[tuple[LoginSession, Membership], Depends(identity)]


def require_editor(auth):
    if auth[1].role not in {'owner', 'editor'}:
        raise HTTPException(403, 'Seu papel permite apenas leitura.')


def describe(db, session, membership):
    user = db.get(User, session.user_id)
    workspace = db.get(Workspace, session.workspace_id)
    return {'user': {'id': user.id, 'email': user.email, 'country': user.country},
            'workspace': {'id': workspace.id, 'name': workspace.name, 'role': membership.role},
            'csrf_token': session.csrf}


class Login(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(min_length=1, max_length=1024)


@router.post('/auth/login')
def login(body: Login, request: Request, response: Response, db=Depends(database)):
    if request.headers.get('origin') not in {None, request.app.state.settings.origin}:
        raise HTTPException(403, 'Origem inválida.')
    user = db.scalar(select(User).where(User.email == body.email.strip().lower()))
    valid = passwords.verify(body.password, user.password_hash if user else dummy_hash)
    if not valid or user is None:
        raise HTTPException(401, 'Email ou senha inválidos.')
    membership = db.scalar(select(Membership).where(Membership.user_id == user.id)
                           .order_by(Membership.workspace_id))
    if membership is None:
        raise HTTPException(403, 'Nenhum workspace disponível.')
    token = token_urlsafe(32)
    session = LoginSession(token_hash=digest(token), user_id=user.id, workspace_id=membership.workspace_id,
                           csrf=token_urlsafe(32), expires_at=now() + timedelta(hours=24))
    db.add(session)
    response.set_cookie('pulso_session', token, httponly=True, samesite='lax',
                        secure=request.app.state.settings.cookie_secure, max_age=86400, path='/')
    return describe(db, session, membership)


@router.get('/auth/me')
def me(auth: Identity, db=Depends(database)):
    return describe(db, *auth)


@router.post('/auth/logout')
def logout(auth: Identity, response: Response, db=Depends(database)):
    db.delete(auth[0])
    response.delete_cookie('pulso_session', path='/')
    return {'ok': True}


class Preference(BaseModel):
    country: str = Field(min_length=2, max_length=2)


@router.patch('/preferences')
def preferences(body: Preference, auth: Identity, db=Depends(database)):
    if not pycountry.countries.get(alpha_2=body.country):
        raise HTTPException(422, 'País inválido.')
    db.get(User, auth[0].user_id).country = body.country
    return {'country': body.country}
