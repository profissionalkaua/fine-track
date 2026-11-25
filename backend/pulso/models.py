from datetime import datetime

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base, now, uid


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    country: Mapped[str] = mapped_column(String(2), default="BR")


class Workspace(Base):
    __tablename__ = "workspaces"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(160))


class Membership(Base):
    __tablename__ = "memberships"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), primary_key=True)
    role: Mapped[str] = mapped_column(String(10), default="owner")


class LoginSession(Base):
    __tablename__ = "sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"))
    csrf: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Video(Base):
    __tablename__ = "videos"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    creator_id: Mapped[str] = mapped_column(String(64), index=True)
    handle: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(Text)
    thumbnail: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    country: Mapped[str | None] = mapped_column(String(2), index=True)
    geo_evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    categories: Mapped[list] = mapped_column(JSON, default=list)
    hashtags: Mapped[list] = mapped_column(JSON, default=list)
    available: Mapped[bool] = mapped_column(Boolean, default=True)
    duration: Mapped[float | None]
    synthetic: Mapped[bool] = mapped_column(Boolean, default=False)


class Snapshot(Base):
    __tablename__ = "metric_snapshots"
    __table_args__ = (UniqueConstraint("video_id", "observed_at", "source"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    video_id: Mapped[str] = mapped_column(ForeignKey("videos.id"), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    views: Mapped[int | None] = mapped_column(BigInteger)
    likes: Mapped[int | None] = mapped_column(BigInteger)
    comments: Mapped[int | None] = mapped_column(BigInteger)
    shares: Mapped[int | None] = mapped_column(BigInteger)
    source: Mapped[str] = mapped_column(String(40), default="tiktok-api")


class Ranking(Base):
    __tablename__ = "rankings"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    country: Mapped[str] = mapped_column(String(2), index=True)
    period: Mapped[str] = mapped_column(String(10))
    category: Mapped[str] = mapped_column(String(250), default="")
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)
    algorithm: Mapped[str] = mapped_column(String(24), default="velocity-v1")
    items: Mapped[list] = mapped_column(JSON, default=list)
    most_viewed: Mapped[list] = mapped_column(JSON, default=list)
