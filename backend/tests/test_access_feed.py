def test_login_opens_workspace_and_empty_feed():
    from fastapi.testclient import TestClient

    from pulso.admin import migrate, provision
    from pulso.config import Settings
    from pulso.main import create_app

    settings = Settings.testing()
    migrate(settings, reset=True)
    provision(settings, "owner@example.test", "a-secure-test-password", "Estúdio de teste")
    with TestClient(create_app(settings)) as client:
        assert client.get("/v1/top-videos").status_code == 401
        login = client.post(
            "/v1/auth/login",
            json={
                "email": "owner@example.test",
                "password": "a-secure-test-password",
            },
        )
        assert login.status_code == 200
        assert login.json()["workspace"]["name"] == "Estúdio de teste"
        feed = client.get("/v1/top-videos")
        assert feed.status_code == 200
        assert feed.json()["items"] == []
        assert feed.json()["country"] == "BR"
        assert feed.json()["coverage_status"] == "source_unavailable"
