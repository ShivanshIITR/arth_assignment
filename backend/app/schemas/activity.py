from datetime import datetime
from typing import Any, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import ActivityEventType
from app.schemas.user import UserRead


class ActivityLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    actor_id: UUID | None
    actor: UserRead | None = None
    event_type: ActivityEventType
    task_id: UUID | None
    metadata: dict[str, Any] | None = None
    created_at: datetime

    @classmethod
    def from_entry(cls, entry) -> Self:
        return cls(
            id=entry.id,
            project_id=entry.project_id,
            actor_id=entry.actor_id,
            actor=UserRead.model_validate(entry.actor) if entry.actor else None,
            event_type=entry.event_type,
            task_id=entry.task_id,
            metadata=entry.event_metadata,
            created_at=entry.created_at,
        )
