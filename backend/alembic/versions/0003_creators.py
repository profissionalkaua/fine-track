"""Creator identity and workspace references."""

import sqlalchemy as sa

from alembic import op

revision = "0003"
down_revision = "0002"


def upgrade():
    op.create_table(
        "creators",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("handle", sa.String(80), nullable=False, index=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("available", sa.Boolean, nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "workspace_creators",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id"), nullable=False, index=True),
        sa.Column("creator_id", sa.String(64), sa.ForeignKey("creators.id")),
        sa.Column("handle", sa.String(80), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("previous_status", sa.String(20)),
        sa.Column("error", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("workspace_id", "handle"),
        sa.UniqueConstraint("workspace_id", "creator_id"),
    )
    op.execute("ALTER TABLE workspace_creators ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE workspace_creators FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY workspace_isolation ON workspace_creators USING "
        "(workspace_id = current_setting('pulso.workspace_id', true)) "
        "WITH CHECK (workspace_id = current_setting('pulso.workspace_id', true))"
    )


def downgrade():
    op.drop_table("workspace_creators")
    op.drop_table("creators")
