"""Immutable brand revisions."""

import sqlalchemy as sa

from alembic import op

revision = "0004"
down_revision = "0003"


def upgrade():
    op.create_table(
        "brand_rule_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id"), nullable=False, index=True),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("category_text", sa.String(250)),
        sa.Column("category_key", sa.String(250), nullable=False),
        sa.Column("content", sa.JSON, nullable=False),
        sa.Column("author_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("workspace_id", "version"),
    )
    op.execute("ALTER TABLE brand_rule_versions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE brand_rule_versions FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY workspace_isolation ON brand_rule_versions USING "
        "(workspace_id = current_setting('pulso.workspace_id', true)) "
        "WITH CHECK (workspace_id = current_setting('pulso.workspace_id', true))"
    )


def downgrade():
    op.drop_table("brand_rule_versions")
