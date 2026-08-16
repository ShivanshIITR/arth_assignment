from datetime import datetime
from typing import Any, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import AuditEventType
from app.schemas.user import UserRead


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    actor_id: UUID | None
    actor: UserRead | None = None
    event_type: AuditEventType
    project_id: UUID | None
    resource_type: str | None
    resource_id: UUID | None
    metadata: dict[str, Any] | None = None
    ip_address: str | None = None
    created_at: datetime

    @classmethod
    def from_entry(cls, entry) -> Self:
        return cls(
            id=entry.id,
            actor_id=entry.actor_id,
            actor=UserRead.model_validate(entry.actor) if entry.actor else None,
            event_type=entry.event_type,
            project_id=entry.project_id,
            resource_type=entry.resource_type,
            resource_id=entry.resource_id,
            metadata=entry.event_metadata,
            ip_address=str(entry.ip_address) if entry.ip_address else None,
            created_at=entry.created_at,
        )
