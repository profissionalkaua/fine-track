from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session


def now():
    return datetime.now(UTC)


def uid():
    return str(uuid4())


class Base(DeclarativeBase):
    pass


def engine_for(url: str):
    return create_engine(url, pool_pre_ping=True, pool_size=5)


def session_for(engine):
    return Session(engine, expire_on_commit=False)
