from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from pulso.admin import migrate, provision
from pulso.config import Settings
from pulso.main import create_app

AS_OF = datetime(2026, 11, 25, 12, tzinfo=UTC)


@pytest.fixture
def settings():
    return Settings.testing()


@pytest.fixture
def client(settings):
    migrate(settings, reset=True)
    provision(settings, "owner@example.test", "a-secure-test-password", "Estúdio de teste")
    app = create_app(settings)
    app.state.clock = lambda: AS_OF
    with TestClient(app) as client:
        result = client.post(
            "/v1/auth/login", json={"email": "owner@example.test", "password": "a-secure-test-password"}
        )
        client.headers["x-csrf-token"] = result.json()["csrf_token"]
        yield client


def observation(
    video_id="9000000000000000001",
    *,
    views=1000,
    end_views=45000,
    country="BR",
    category="Culinária",
    tags=None,
):
    return {
        "id": video_id,
        "creator_id": "creator-1",
        "handle": "cozinha.teste",
        "description": "Uma receita prática para a semana",
        "url": None,
        "thumbnail": None,
        "published_at": "2026-11-20T12:00:00+00:00",
        "country": country,
        "geo_evidence": {"kind": "observed", "reason": "País declarado pela fonte", "confidence": 1},
        "categories": [{"text": category, "confidence": 0.95, "version": "review-v1"}],
        "hashtags": tags or ["receitas"],
        "duration": None,
        "synthetic": True,
        "snapshots": [
            {
                "observed_at": "2026-11-24T14:00:00+00:00",
                "views": views,
                "likes": None,
                "comments": 12,
                "shares": None,
                "source": "fixture",
            },
            {
                "observed_at": "2026-11-25T12:00:00+00:00",
                "views": end_views,
                "likes": None,
                "comments": 20,
                "shares": None,
                "source": "fixture",
            },
        ],
    }
