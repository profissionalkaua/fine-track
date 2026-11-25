"""Shared source cache and observation provenance."""

import sqlalchemy as sa

from alembic import op

revision = "0008"
down_revision = "0007"


def upgrade():
    op.create_table(
        "collection_cache",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON, nullable=False),
    )
    op.create_table(
        "source_observations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("video_id", sa.String(32), sa.ForeignKey("videos.id"), nullable=False, index=True),
        sa.Column("source", sa.String(40), nullable=False),
        sa.Column("reference", sa.String(300), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("adapter_version", sa.String(50), nullable=False),
        sa.Column("evidence", sa.JSON, nullable=False),
        sa.UniqueConstraint("video_id", "source", "reference", "observed_at"),
    )


def downgrade():
    op.drop_table("source_observations")
    op.drop_table("collection_cache")
