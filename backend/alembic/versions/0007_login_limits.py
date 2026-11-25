"""Shared login throttling."""

import sqlalchemy as sa

from alembic import op

revision = "0007"
down_revision = "0006"


def upgrade():
    op.create_table(
        "login_attempts",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("attempts", sa.Integer, nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade():
    op.drop_table("login_attempts")
