from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.project_member import ProjectMember
from app.schemas.user import UserRead


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=4000)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=4000)


class ProjectMemberAdd(BaseModel):
    email: EmailStr


class ProjectMemberRead(BaseModel):
    user_id: UUID
    email: EmailStr
    full_name: str
    joined_at: datetime

    @classmethod
    def from_member(cls, member: ProjectMember) -> Self:
        return cls(
            user_id=member.user_id,
            email=member.user.email,
            full_name=member.user.full_name,
            joined_at=member.joined_at,
        )


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    owner_id: UUID
    owner: UserRead
    members: list[ProjectMemberRead]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_project(cls, project) -> Self:
        return cls(
            id=project.id,
            name=project.name,
            description=project.description,
            owner_id=project.owner_id,
            owner=UserRead.model_validate(project.owner),
            members=[
                ProjectMemberRead.from_member(member) for member in project.members
            ],
            created_at=project.created_at,
            updated_at=project.updated_at,
        )
