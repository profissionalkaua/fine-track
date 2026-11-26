"""Workspace-authorized media and scoped analysis cache."""

import sqlalchemy as sa

from alembic import op

revision = "0006"
down_revision = "0005"


def upgrade():
    op.create_table(
        "authorized_media",
        sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id"), primary_key=True),
        sa.Column("video_id", sa.String(32), sa.ForeignKey("videos.id"), primary_key=True),
        sa.Column("path", sa.Text, nullable=False),
        sa.Column("media_hash", sa.String(64), nullable=False),
        sa.Column("rights_reference", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "video_analyses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id"), nullable=False, index=True),
        sa.Column("video_id", sa.String(32), sa.ForeignKey("videos.id"), nullable=False),
        sa.Column("cache_key", sa.String(64), nullable=False),
        sa.Column("result", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("workspace_id", "video_id", "cache_key"),
    )
    for table in ["authorized_media", "video_analyses"]:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY workspace_isolation ON {table} USING "
            "(workspace_id = current_setting('pulso.workspace_id', true)) "
            "WITH CHECK (workspace_id = current_setting('pulso.workspace_id', true))"
        )


def downgrade():
    op.drop_table("video_analyses")
    op.drop_table("authorized_media")
