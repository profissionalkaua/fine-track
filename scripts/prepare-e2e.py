"""Opt-in demo user and synthetic data for local browser tests only."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from pulso.admin import migrate, provision
from pulso.config import Settings
from pulso.fixtures import seed

settings = Settings()
if settings.environment != "development" or "127.0.0.1" not in settings.database_url:
    raise SystemExit(
        "Preparação de testes permitida somente no banco local de desenvolvimento."
    )
migrate(settings)
provision(settings, "demo@pulso.local", "pulso-demo-local-2026", "Estúdio Pulso")
provision(settings, "demo@pulso.local", "pulso-demo-local-2026", "Estúdio Alternativo")
from pulso.auth import digest
from pulso.db import engine_for, session_for
from pulso.models import LoginAttempt
from sqlalchemy import delete

engine = engine_for(settings.admin_database_url)
with session_for(engine) as db, db.begin():
    db.execute(
        delete(LoginAttempt).where(
            LoginAttempt.key.in_(
                [digest("127.0.0.1:demo@pulso.local"), digest("ip:127.0.0.1")]
            )
        )
    )
engine.dispose()
seed(settings)
print("Ambiente de navegador preparado com dados fictícios.")
