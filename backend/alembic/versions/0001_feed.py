"""Identity and public observation storage."""

import sqlalchemy as sa

from alembic import op

revision = "0001"
down_revision = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(254), nullable=False, unique=True),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("country", sa.String(2), nullable=False),
    )
    op.create_table(
        "workspaces",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(160), nullable=False),
    )
    op.create_table(
        "memberships",
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id"), primary_key=True),
        sa.Column("role", sa.String(10), nullable=False),
    )
    op.create_table(
        "sessions",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("csrf", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "videos",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("creator_id", sa.String(64), nullable=False, index=True),
        sa.Column("handle", sa.String(80), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("url", sa.Text),
        sa.Column("thumbnail", sa.Text),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("country", sa.String(2), index=True),
        sa.Column("geo_evidence", sa.JSON, nullable=False),
        sa.Column("categories", sa.JSON, nullable=False),
        sa.Column("hashtags", sa.JSON, nullable=False),
        sa.Column("available", sa.Boolean, nullable=False),
        sa.Column("duration", sa.Float),
        sa.Column("synthetic", sa.Boolean, nullable=False),
    )
    op.create_table(
        "metric_snapshots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("video_id", sa.String(32), sa.ForeignKey("videos.id"), nullable=False, index=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("views", sa.BigInteger),
        sa.Column("likes", sa.BigInteger),
        sa.Column("comments", sa.BigInteger),
        sa.Column("shares", sa.BigInteger),
        sa.Column("source", sa.String(40), nullable=False),
        sa.UniqueConstraint("video_id", "observed_at", "source"),
    )
    op.create_table(
        "rankings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("country", sa.String(2), nullable=False, index=True),
        sa.Column("period", sa.String(10), nullable=False),
        sa.Column("category", sa.String(250), nullable=False),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("algorithm", sa.String(24), nullable=False),
        sa.Column("items", sa.JSON, nullable=False),
        sa.Column("most_viewed", sa.JSON, nullable=False),
    )


def downgrade():
    for name in ["rankings", "metric_snapshots", "videos", "sessions", "memberships", "workspaces", "users"]:
        op.drop_table(name)
