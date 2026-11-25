"""Public administrative entry points; run only with migration credentials."""

import argparse
import getpass
from pathlib import Path

from alembic.config import Config
from pwdlib import PasswordHash
from sqlalchemy import select, text

from alembic import command

from .config import Settings
from .db import engine_for, session_for
from .models import Membership, User, Workspace


def migrate(settings: Settings, reset=False):
    engine = engine_for(settings.admin_database_url)
    if reset:
        if settings.environment != "test" or not engine.url.database.endswith("_test"):
            raise ValueError("Reset permitido somente no banco isolado de testes.")
        with engine.begin() as conn:
            conn.execute(text("DROP SCHEMA public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))
    cfg = Config(str(Path(__file__).parent.parent / "alembic.ini"))
    cfg.set_main_option("script_location", str(Path(__file__).parent.parent / "alembic"))
    cfg.set_main_option("sqlalchemy.url", settings.admin_database_url)
    command.upgrade(cfg, "head")
    with engine.begin() as conn:
        exists = conn.execute(text("SELECT 1 FROM pg_roles WHERE rolname='pulso_app'")).scalar()
        if not exists:
            # PostgreSQL utility statements cannot use bind parameters for role passwords.
            quoted = (
                conn.dialect.identifier_preparer.quote_literal(settings.app_role_password)
                if hasattr(conn.dialect.identifier_preparer, "quote_literal")
                else "'" + settings.app_role_password.replace("'", "''") + "'"
            )
            conn.execute(text(f"CREATE ROLE pulso_app LOGIN PASSWORD {quoted} NOSUPERUSER NOBYPASSRLS"))
        conn.execute(text("GRANT USAGE ON SCHEMA public TO pulso_app"))
        conn.execute(text("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO pulso_app"))
        conn.execute(text("REVOKE ALL ON alembic_version FROM pulso_app"))
    engine.dispose()


def provision(
    settings: Settings,
    email: str,
    password: str,
    workspace_name: str,
    role="owner",
    workspace_id: str | None = None,
):
    if role not in {"owner", "editor", "viewer"} or len(password) < 12:
        raise ValueError("Papel inválido ou senha com menos de 12 caracteres.")
    engine = engine_for(settings.admin_database_url)
    with session_for(engine) as db, db.begin():
        user = db.scalar(select(User).where(User.email == email.strip().lower()))
        if user is None:
            user = User(email=email.strip().lower(), password_hash=PasswordHash.recommended().hash(password))
            db.add(user)
            db.flush()
        if workspace_id:
            workspace = db.get(Workspace, workspace_id)
        else:
            workspace = db.scalar(
                select(Workspace)
                .join(Membership, Membership.workspace_id == Workspace.id)
                .where(Membership.user_id == user.id, Workspace.name == workspace_name)
                .order_by(Workspace.id)
            )
            workspace = workspace or Workspace(name=workspace_name)
        if workspace is None:
            raise ValueError("Workspace inexistente.")
        db.add(workspace)
        db.flush()
        if db.get(Membership, (user.id, workspace.id)) is None:
            db.add(Membership(user_id=user.id, workspace_id=workspace.id, role=role))
        result = {"user_id": user.id, "workspace_id": workspace.id}
    engine.dispose()
    return result


def main():
    parser = argparse.ArgumentParser(description="Administração local do Pulso")
    parser.add_argument(
        "command", choices=["migrate", "user", "seed", "attach-media", "review-category", "resume-source"]
    )
    parser.add_argument("--email")
    parser.add_argument("--workspace", default="Meu estúdio")
    parser.add_argument("--workspace-id")
    parser.add_argument("--role", default="owner", choices=["owner", "editor", "viewer"])
    parser.add_argument("--video-id", action="append", default=[])
    parser.add_argument("--file")
    parser.add_argument("--rights-reference")
    parser.add_argument("--category")
    args = parser.parse_args()
    settings = Settings()
    if args.command == "migrate":
        migrate(settings)
        print("Migrações aplicadas.")
    elif args.command == "user":
        email = args.email or input("Email: ")
        print(
            provision(
                settings,
                email,
                getpass.getpass("Senha (mínimo 12 caracteres): "),
                args.workspace,
                args.role,
                args.workspace_id,
            )
        )
    elif args.command == "seed":
        from .fixtures import seed

        seed(settings)
        print("Amostra fictícia carregada em desenvolvimento.")
    elif args.command == "attach-media":
        if not args.workspace_id or len(args.video_id) != 1 or not args.file or not args.rights_reference:
            parser.error("Informe --workspace-id, --video-id, --file e --rights-reference.")
        register_media(settings, args.workspace_id, args.video_id[0], args.file, args.rights_reference)
        print("Versão da mídia e autorização registradas no workspace.")
    elif args.command == "review-category":
        if not args.video_id or not args.category or len(args.category.strip()) > 250:
            parser.error("Informe --video-id e uma --category de até 250 caracteres.")
        from .db import now
        from .models import Video

        engine = engine_for(settings.admin_database_url)
        with session_for(engine) as db, db.begin():
            for video_id in args.video_id:
                video = db.get(Video, video_id)
                if video is None:
                    raise ValueError("Vídeo não encontrado.")
                video.categories = [
                    *video.categories,
                    {
                        "text": args.category.strip(),
                        "reviewed": True,
                        "confidence": 1,
                        "version": f"human-{now().date()}",
                    },
                ]
        engine.dispose()
        print("Classificação revisada registrada. Atualize os rankings pela próxima coleta.")
    else:
        from .models import SourceHealth

        engine = engine_for(settings.admin_database_url)
        with session_for(engine) as db, db.begin():
            state = db.get(SourceHealth, "tiktok")
            if state:
                state.suspended, state.reason, state.retry_at = False, None, None
        engine.dispose()
        print("Suspensão da fonte removida após revisão do operador.")


def load_observations(settings: Settings, records: list[dict], as_of=None):
    """Administrative ingestion uses the same normalization persistence as collection."""
    from .feed import ingest_records, publish_ranking

    engine = engine_for(settings.admin_database_url)
    try:
        with session_for(engine) as db, db.begin():
            ingest_records(db, records, allow_synthetic=settings.environment in {"development", "test"})
            for country in {record["country"] for record in records if record.get("country")}:
                for period in ["day", "week", "month"]:
                    publish_ranking(
                        db, country, period, as_of=as_of, freshness=settings.latest_snapshot_hours
                    )
    finally:
        engine.dispose()


def register_media(settings, workspace_id, video_id, path, rights_reference):
    import hashlib

    from .adapters.media import MediaAnalyzer
    from .models import AuthorizedMedia, Video

    if not rights_reference.strip():
        raise ValueError("Registre a referência de autorização de processamento.")
    path = MediaAnalyzer(settings).authorized_file(path)
    engine = engine_for(settings.admin_database_url)
    with session_for(engine) as db, db.begin():
        if not db.get(Workspace, workspace_id) or not db.get(Video, video_id):
            raise ValueError("Workspace ou vídeo inexistente.")
        db.merge(
            AuthorizedMedia(
                workspace_id=workspace_id,
                video_id=video_id,
                path=str(path),
                media_hash=hashlib.sha256(path.read_bytes()).hexdigest(),
                rights_reference=rights_reference,
            )
        )
    engine.dispose()


if __name__ == "__main__":
    main()
