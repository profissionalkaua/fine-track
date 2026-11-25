from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
import pycountry

from .auth import Identity, database, router as auth_router
from .config import Settings
from .db import engine_for, now
from .feed import get_feed
from .models import User


def create_app(settings: Settings | None = None):
    settings = settings or Settings()
    if settings.environment == 'production' and (not settings.cookie_secure or 'local-only' in settings.database_url):
        raise ValueError('Configure credenciais próprias e cookies seguros em produção.')

    @asynccontextmanager
    async def lifespan(app):
        yield
        app.state.engine.dispose()

    app = FastAPI(title='Pulso', version='0.1.0', lifespan=lifespan)
    app.state.settings = settings
    app.state.engine = engine_for(settings.database_url)
    app.state.clock = now
    app.include_router(auth_router)

    @app.get('/health')
    def health():
        return {'status': 'ok'}

    @app.get('/v1/countries')
    def countries(auth: Identity):
        return [{'code': c.alpha_2, 'name': c.name} for c in sorted(pycountry.countries, key=lambda c: c.name)]

    @app.get('/v1/top-videos')
    def top(auth: Identity, request: Request, country: str | None = None, period: str = 'day',
            limit: int = 20, cursor: str | None = None, db=Depends(database)):
        country = country or db.get(User, auth[0].user_id).country
        if not pycountry.countries.get(alpha_2=country) or period not in {'day', 'week', 'month'}:
            raise HTTPException(422, 'País ou período inválido.')
        return get_feed(db, country, period, None, limit, cursor, request.app.state.clock(), settings)

    return app
