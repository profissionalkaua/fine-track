from contextlib import asynccontextmanager

import pycountry
from fastapi import Depends, FastAPI, HTTPException, Request

from .auth import Identity, database
from .auth import router as auth_router
from .config import Settings
from .db import engine_for, now
from .feed import get_feed
from .models import User


def create_app(settings: Settings | None = None):
    settings = settings or Settings()
    if settings.environment == "production" and (
        not settings.cookie_secure or "local-only" in settings.database_url
    ):
        raise ValueError("Configure credenciais próprias e cookies seguros em produção.")

    @asynccontextmanager
    async def lifespan(app):
        yield
        app.state.engine.dispose()

    app = FastAPI(title="Pulso", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.engine = engine_for(settings.database_url)
    app.state.clock = now
    from .adapters.tiktok import TikTokCollector

    app.state.collector = TikTokCollector(settings)
    from .adapters.ollama import OllamaGenerator

    app.state.generator = OllamaGenerator(settings)
    from .adapters.classifier import MetadataClassifier

    app.state.classifier = MetadataClassifier(settings)
    from .monitoring import install

    install(app, settings)
    app.include_router(auth_router)
    from .creators import router as creators_router

    app.include_router(creators_router)
    from .brands import current_rules
    from .brands import router as brands_router

    app.include_router(brands_router)
    from .runs import router as runs_router

    app.include_router(runs_router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/v1/countries")
    def countries(auth: Identity):
        return [
            {"code": c.alpha_2, "name": c.name} for c in sorted(pycountry.countries, key=lambda c: c.name)
        ]

    @app.get("/v1/top-videos")
    def top(
        auth: Identity,
        request: Request,
        country: str | None = None,
        period: str = "day",
        limit: int = 20,
        cursor: str | None = None,
        db=Depends(database, scope="function"),
    ):
        country = country or db.get(User, auth[0].user_id).country
        if not pycountry.countries.get(alpha_2=country) or period not in {"day", "week", "month"}:
            raise HTTPException(422, "País ou período inválido.")
        rules = current_rules(db)
        category = rules.category_text if rules else None
        result = get_feed(db, country, period, category, limit, cursor, request.app.state.clock(), settings)
        app.state.metrics.eligible.labels(country, period).observe(result["eligible_count"])
        if (
            settings.collection_enabled
            and (not result["version"] or result["is_stale"] or not result["eligible_count"])
            and not cursor
        ):
            from .jobs import collection_state

            result.update(
                collection_state(
                    db, auth[0].workspace_id, country, period, category, request.app.state.clock(), settings
                )
            )
        return result

    return app
