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


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (UniqueConstraint("workspace_id", "key"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    key: Mapped[str] = mapped_column(String(250))
    kind: Mapped[str] = mapped_column(String(30))
    payload: Mapped[dict] = mapped_column(JSON)
    state: Mapped[str] = mapped_column(String(20), default="queued")
    attempts: Mapped[int] = mapped_column(default=0)
    not_before: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    lease_token: Mapped[str | None] = mapped_column(String(36))
    error: Mapped[str | None] = mapped_column(Text)
    error_kind: Mapped[str | None] = mapped_column(String(30))


class Outbox(Base):
    __tablename__ = "outbox"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), unique=True)
    workspace_id: Mapped[str] = mapped_column(String(36))
    queue: Mapped[str] = mapped_column(String(30))
    not_before: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SourceHealth(Base):
    __tablename__ = "source_health"
    source: Mapped[str] = mapped_column(String(30), primary_key=True)
    suspended: Mapped[bool] = mapped_column(Boolean, default=False)
    reason: Mapped[str | None] = mapped_column(Text)
    retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Creator(Base):
    __tablename__ = "creators"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    handle: Mapped[str] = mapped_column(String(80), index=True)
    name: Mapped[str] = mapped_column(String(160))
    available: Mapped[bool] = mapped_column(Boolean, default=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class WorkspaceCreator(Base):
    __tablename__ = "workspace_creators"
    __table_args__ = (
        UniqueConstraint("workspace_id", "handle"),
        UniqueConstraint("workspace_id", "creator_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    creator_id: Mapped[str | None] = mapped_column(ForeignKey("creators.id"))
    handle: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    previous_status: Mapped[str | None] = mapped_column(String(20))
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class BrandVersion(Base):
    __tablename__ = "brand_rule_versions"
    __table_args__ = (UniqueConstraint("workspace_id", "version"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    version: Mapped[int]
    category_text: Mapped[str | None] = mapped_column(String(250))
    category_key: Mapped[str] = mapped_column(String(250), default="")
    content: Mapped[dict] = mapped_column(JSON)
    author_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Run(Base):
    __tablename__ = "runs"
    __table_args__ = (UniqueConstraint("workspace_id", "idempotency_key"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(128))
    request_hash: Mapped[str] = mapped_column(String(64))
    parent_id: Mapped[str | None] = mapped_column(String(36))
    scope: Mapped[str] = mapped_column(String(10))
    state: Mapped[str] = mapped_column(String(20), default="queued")
    progress: Mapped[int] = mapped_column(default=0)
    processed: Mapped[int] = mapped_column(default=0)
    frozen: Mapped[dict] = mapped_column(JSON)
    result: Mapped[dict | None] = mapped_column(JSON)
    errors: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AuthorizedMedia(Base):
    __tablename__ = "authorized_media"
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), primary_key=True)
    video_id: Mapped[str] = mapped_column(ForeignKey("videos.id"), primary_key=True)
    path: Mapped[str] = mapped_column(Text)
    media_hash: Mapped[str] = mapped_column(String(64))
    rights_reference: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class VideoAnalysis(Base):
    __tablename__ = "video_analyses"
    __table_args__ = (UniqueConstraint("workspace_id", "video_id", "cache_key"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    video_id: Mapped[str] = mapped_column(ForeignKey("videos.id"))
    cache_key: Mapped[str] = mapped_column(String(64))
    result: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class LoginAttempt(Base):
    __tablename__ = "login_attempts"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    attempts: Mapped[int]
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CollectionCache(Base):
    __tablename__ = "collection_cache"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    payload: Mapped[dict] = mapped_column(JSON)


class SourceObservation(Base):
    __tablename__ = "source_observations"
    __table_args__ = (UniqueConstraint("video_id", "source", "reference", "observed_at"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    video_id: Mapped[str] = mapped_column(ForeignKey("videos.id"), index=True)
    source: Mapped[str] = mapped_column(String(40))
    reference: Mapped[str] = mapped_column(String(300), default="")
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    adapter_version: Mapped[str] = mapped_column(String(50))
    evidence: Mapped[dict] = mapped_column(JSON)
