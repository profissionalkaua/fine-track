"""Public administrative entry points; run only with migration credentials."""
import argparse
import getpass
from pathlib import Path

from alembic import command
from alembic.config import Config
from pwdlib import PasswordHash
from sqlalchemy import select, text

from .config import Settings
from .db import engine_for, session_for
from .models import Membership, User, Workspace


def migrate(settings: Settings, reset=False):
    engine = engine_for(settings.admin_database_url)
    if reset:
        if settings.environment != 'test' or not engine.url.database.endswith('_test'):
            raise ValueError('Reset permitido somente no banco isolado de testes.')
        with engine.begin() as conn:
            conn.execute(text('DROP SCHEMA public CASCADE'))
            conn.execute(text('CREATE SCHEMA public'))
    cfg = Config(str(Path(__file__).parent.parent / 'alembic.ini'))
    cfg.set_main_option('script_location', str(Path(__file__).parent.parent / 'alembic'))
    cfg.set_main_option('sqlalchemy.url', settings.admin_database_url)
    command.upgrade(cfg, 'head')
    with engine.begin() as conn:
        exists = conn.execute(text("SELECT 1 FROM pg_roles WHERE rolname='pulso_app'")).scalar()
        if not exists:
            # PostgreSQL utility statements cannot use bind parameters for role passwords.
            quoted = conn.dialect.identifier_preparer.quote_literal(settings.app_role_password) if hasattr(
                conn.dialect.identifier_preparer, 'quote_literal') else "'" + settings.app_role_password.replace("'", "''") + "'"
            conn.execute(text(f'CREATE ROLE pulso_app LOGIN PASSWORD {quoted} NOSUPERUSER NOBYPASSRLS'))
        conn.execute(text('GRANT USAGE ON SCHEMA public TO pulso_app'))
        conn.execute(text('GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO pulso_app'))
        conn.execute(text('REVOKE ALL ON alembic_version FROM pulso_app'))
    engine.dispose()


def provision(settings: Settings, email: str, password: str, workspace_name: str,
              role='owner', workspace_id: str | None = None):
    if role not in {'owner', 'editor', 'viewer'} or len(password) < 12:
        raise ValueError('Papel inválido ou senha com menos de 12 caracteres.')
    engine = engine_for(settings.admin_database_url)
    with session_for(engine) as db, db.begin():
        user = db.scalar(select(User).where(User.email == email.strip().lower()))
        if user is None:
            user = User(email=email.strip().lower(), password_hash=PasswordHash.recommended().hash(password))
            db.add(user)
            db.flush()
        workspace = db.get(Workspace, workspace_id) if workspace_id else Workspace(name=workspace_name)
        if workspace is None:
            raise ValueError('Workspace inexistente.')
        db.add(workspace)
        db.flush()
        if db.get(Membership, (user.id, workspace.id)) is None:
            db.add(Membership(user_id=user.id, workspace_id=workspace.id, role=role))
        result = {'user_id': user.id, 'workspace_id': workspace.id}
    engine.dispose()
    return result


def main():
    parser = argparse.ArgumentParser(description='Administração local do Pulso')
    parser.add_argument('command', choices=['migrate', 'user', 'seed'])
    parser.add_argument('--email')
    parser.add_argument('--workspace', default='Meu estúdio')
    parser.add_argument('--workspace-id')
    parser.add_argument('--role', default='owner', choices=['owner', 'editor', 'viewer'])
    args = parser.parse_args()
    settings = Settings()
    if args.command == 'migrate':
        migrate(settings)
        print('Migrações aplicadas.')
    elif args.command == 'user':
        email = args.email or input('Email: ')
        print(provision(settings, email, getpass.getpass('Senha (mínimo 12 caracteres): '), args.workspace,
                        args.role, args.workspace_id))
    else:
        from .fixtures import seed
        seed(settings)
        print('Amostra fictícia carregada em desenvolvimento.')


if __name__ == '__main__':
    main()


def load_observations(settings: Settings, records: list[dict], as_of=None):
    """Load normalized observations through the administrative ingestion boundary."""
    from datetime import datetime
    from .feed import publish_ranking
    from .models import Snapshot, Video

    engine = engine_for(settings.admin_database_url)
    with session_for(engine) as db, db.begin():
        for record in records:
            if record.get('synthetic') and settings.environment not in {'development', 'test'}:
                raise ValueError('Fixtures são proibidas neste ambiente.')
            data = {k: v for k, v in record.items() if k != 'snapshots'}
            if isinstance(data['published_at'], str):
                data['published_at'] = datetime.fromisoformat(data['published_at'])
            db.merge(Video(**data))
            db.flush()
            for sample in record.get('snapshots', []):
                sample = dict(sample)
                if isinstance(sample['observed_at'], str):
                    sample['observed_at'] = datetime.fromisoformat(sample['observed_at'])
                existing = db.scalar(select(Snapshot).where(Snapshot.video_id == record['id'],
                        Snapshot.observed_at == sample['observed_at'], Snapshot.source == sample['source']))
                if existing is None:
                    db.add(Snapshot(video_id=record['id'], **sample))
        db.flush()
        for country in {r['country'] for r in records if r.get('country')}:
            for period in ['day', 'week', 'month']:
                publish_ranking(db, country, period, as_of=as_of)
    engine.dispose()
