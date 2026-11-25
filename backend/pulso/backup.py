"""Explicit backup and isolated restore verification; never overwrites a database."""

import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from .config import Settings
from .db import now


def executable(name):
    found = shutil.which(name)
    if found:
        return found
    local = (
        Path(__file__).resolve().parents[2]
        / "node_modules/@embedded-postgres/windows-x64/native/bin"
        / f"{name}.exe"
    )
    for candidate in [
        local,
        Path(__file__).resolve().parents[2] / ".runtime/postgresql-tools/pgsql/bin" / f"{name}.exe",
    ]:
        if candidate.is_file():
            return str(candidate)
    raise RuntimeError(f"{name} não encontrado. Instale as ferramentas PostgreSQL da versão do servidor.")


def connection_env(settings, database=None):
    url = make_url(settings.admin_database_url)
    return {
        **os.environ,
        "PGHOST": url.host or "localhost",
        "PGPORT": str(url.port or 5432),
        "PGUSER": url.username or "postgres",
        "PGPASSWORD": url.password or "",
        "PGDATABASE": database or url.database,
        "PGCLIENTENCODING": "UTF8",
    }


def backup(settings, destination):
    destination = Path(destination).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise ValueError("O arquivo já existe. Escolha outro destino para preservar o backup anterior.")
    subprocess.run(
        [
            executable("pg_dump"),
            "--format=custom",
            "--no-owner",
            "--no-privileges",
            "--file",
            str(destination),
        ],
        env=connection_env(settings),
        check=True,
        timeout=300,
    )
    destination.with_suffix(".manifest.json").write_text(
        json.dumps(
            {
                "created_at": now().isoformat(),
                "schema_version": "1.0",
                "size_bytes": destination.stat().st_size,
            },
            indent=2,
        ),
        encoding="utf8",
    )
    return destination


def restore_check(settings, source, database):
    if not re.fullmatch(r"pulso_restore_[a-z0-9_]{1,50}", database):
        raise ValueError("A restauração de teste exige um novo banco pulso_restore_<identificador>.")
    source = Path(source).resolve()
    if not source.is_file():
        raise ValueError("Backup não encontrado.")
    engine = create_engine(settings.admin_database_url, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        if conn.execute(text("SELECT 1 FROM pg_database WHERE datname=:name"), {"name": database}).scalar():
            raise ValueError("O banco já existe. A verificação não sobrescreve bancos.")
        conn.execute(text(f'CREATE DATABASE "{database}"'))
    engine.dispose()
    subprocess.run(
        [
            executable("pg_restore"),
            "--dbname",
            database,
            "--no-owner",
            "--no-privileges",
            "--exit-on-error",
            str(source),
        ],
        env=connection_env(settings, database),
        check=True,
        timeout=300,
    )
    url = make_url(settings.admin_database_url).set(database=database)
    restored = create_engine(url)
    with restored.connect() as conn:
        revision = conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        counts = {
            name: conn.execute(text(f"SELECT COUNT(*) FROM {name}")).scalar_one()
            for name in ["users", "workspaces", "videos", "runs"]
        }
    restored.dispose()
    return {"database": database, "revision": revision, "counts": counts, "status": "restored"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backup e restauração isolada do Pulso")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("create").add_argument("destination")
    check = sub.add_parser("check")
    check.add_argument("source")
    check.add_argument("database")
    args = parser.parse_args()
    print(
        backup(Settings(), args.destination)
        if args.command == "create"
        else json.dumps(restore_check(Settings(), args.source, args.database), ensure_ascii=False)
    )
