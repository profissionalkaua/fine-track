"""Frozen analysis executions and results."""

import sqlalchemy as sa

from alembic import op

revision = "0005"
down_revision = "0004"


def upgrade():
    op.create_table(
        "runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id"), nullable=False, index=True),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("parent_id", sa.String(36)),
        sa.Column("scope", sa.String(10), nullable=False),
        sa.Column("state", sa.String(20), nullable=False),
        sa.Column("progress", sa.Integer, nullable=False),
        sa.Column("processed", sa.Integer, nullable=False),
        sa.Column("frozen", sa.JSON, nullable=False),
        sa.Column("result", sa.JSON),
        sa.Column("errors", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("workspace_id", "idempotency_key"),
    )
    op.execute("ALTER TABLE runs ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE runs FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY workspace_isolation ON runs USING "
        "(workspace_id = current_setting('pulso.workspace_id', true)) "
        "WITH CHECK (workspace_id = current_setting('pulso.workspace_id', true))"
    )


def downgrade():
    op.drop_table("runs")
