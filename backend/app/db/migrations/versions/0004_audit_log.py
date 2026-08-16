"""Add audit_logs table.

Revision ID: 0004_audit_log
Revises: 0003_activity_log
Create Date: 2026-08-16

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_audit_log"
down_revision: Union[str, None] = "0003_activity_log"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EVENT_VALUES = (
    "LOGIN",
    "LOGOUT",
    "TOKEN_REUSE_DETECTED",
    "PROJECT_CREATED",
    "PROJECT_UPDATED",
    "PROJECT_DELETED",
    "MEMBER_ADDED",
    "MEMBER_REMOVED",
    "TASK_DELETED",
    "TASK_COMPLETED",
    "ATTACHMENT_UPLOADED",
    "ATTACHMENT_DELETED",
)


def upgrade() -> None:
    values = ", ".join(f"'{value}'" for value in EVENT_VALUES)
    op.execute(
        f"DO $$ BEGIN CREATE TYPE audit_event_type AS ENUM ({values}); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$;"
    )
    audit_event_type = postgresql.ENUM(
        *EVENT_VALUES,
        name="audit_event_type",
        create_type=False,
    )
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", audit_event_type, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resource_type", sa.String(length=50), nullable=True),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["users.id"],
            name="fk_audit_logs_actor_id_users",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_audit_logs_project_id_projects",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_audit_logs"),
    )
    op.create_index(
        "ix_audit_logs_actor_id_created_at",
        "audit_logs",
        ["actor_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_audit_logs_project_id_created_at",
        "audit_logs",
        ["project_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_audit_logs_project_id_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_actor_id_created_at", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.execute("DROP TYPE IF EXISTS audit_event_type")
