from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.user import UserRead


class AttachmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    task_id: UUID
    uploaded_by: UUID
    uploader: UserRead
    original_filename: str
    content_type: str
    size_bytes: int
    created_at: datetime
