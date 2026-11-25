"""Transactional jobs, RLS and public source health."""

import sqlalchemy as sa

from alembic import op

revision = "0002"
down_revision = "0001"


def upgrade():
    op.create_table(
        "jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id"), nullable=False, index=True),
        sa.Column("key", sa.String(250), nullable=False),
        sa.Column("kind", sa.String(30), nullable=False),
        sa.Column("payload", sa.JSON, nullable=False),
        sa.Column("state", sa.String(20), nullable=False),
        sa.Column("attempts", sa.Integer, nullable=False),
        sa.Column("not_before", sa.DateTime(timezone=True), nullable=False),
        sa.Column("lease_until", sa.DateTime(timezone=True)),
        sa.Column("lease_token", sa.String(36)),
        sa.Column("error", sa.Text),
        sa.Column("error_kind", sa.String(30)),
        sa.UniqueConstraint("workspace_id", "key"),
    )
    op.execute("ALTER TABLE jobs ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE jobs FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY workspace_isolation ON jobs USING "
        "(workspace_id = current_setting('pulso.workspace_id', true)) "
        "WITH CHECK (workspace_id = current_setting('pulso.workspace_id', true))"
    )
    # Envelopes contain IDs and scheduling only, never tenant rules or results.
    op.create_table(
        "outbox",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("job_id", sa.String(36), sa.ForeignKey("jobs.id"), nullable=False, unique=True),
        sa.Column("workspace_id", sa.String(36), nullable=False),
        sa.Column("queue", sa.String(30), nullable=False),
        sa.Column("not_before", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "source_health",
        sa.Column("source", sa.String(30), primary_key=True),
        sa.Column("suspended", sa.Boolean, nullable=False),
        sa.Column("reason", sa.Text),
        sa.Column("retry_at", sa.DateTime(timezone=True)),
    )


def downgrade():
    op.drop_table("source_health")
    op.drop_table("outbox")
    op.drop_table("jobs")
