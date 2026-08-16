"""Add activity_logs table.

Revision ID: 0003_activity_log
Revises: 0002_refresh_token_family
Create Date: 2026-08-16

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_activity_log"
down_revision: Union[str, None] = "0002_refresh_token_family"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EVENT_VALUES = (
    "PROJECT_CREATED",
    "PROJECT_UPDATED",
    "MEMBER_ADDED",
    "MEMBER_REMOVED",
    "TASK_CREATED",
    "TASK_ASSIGNED",
    "TASK_STATUS_CHANGED",
    "TASK_UPDATED",
    "TASK_DELETED",
    "TASK_REASSIGNED",
    "ATTACHMENT_UPLOADED",
    "ATTACHMENT_DELETED",
)


def upgrade() -> None:
    values = ", ".join(f"'{value}'" for value in EVENT_VALUES)
    op.execute(
        f"DO $$ BEGIN CREATE TYPE activity_event_type AS ENUM ({values}); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$;"
    )
    activity_event_type = postgresql.ENUM(
        *EVENT_VALUES,
        name="activity_event_type",
        create_type=False,
    )
    op.create_table(
        "activity_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", activity_event_type, nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["users.id"],
            name="fk_activity_logs_actor_id_users",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name="fk_activity_logs_project_id_projects",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["tasks.id"],
            name="fk_activity_logs_task_id_tasks",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_activity_logs"),
    )
    op.create_index(
        "ix_activity_logs_project_id_created_at",
        "activity_logs",
        ["project_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_activity_logs_project_id_created_at", table_name="activity_logs")
    op.drop_table("activity_logs")
    op.execute("DROP TYPE IF EXISTS activity_event_type")
