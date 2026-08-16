from dataclasses import dataclass, field
from uuid import UUID


@dataclass(frozen=True)
class ProjectCreated:
    project_id: UUID
    owner_id: UUID
    actor_id: UUID
    affected_user_ids: tuple[UUID, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ProjectUpdated:
    project_id: UUID
    actor_id: UUID
    affected_user_ids: tuple[UUID, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ProjectDeleted:
    project_id: UUID
    actor_id: UUID
    affected_user_ids: tuple[UUID, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class MemberAdded:
    project_id: UUID
    user_id: UUID
    actor_id: UUID
    affected_user_ids: tuple[UUID, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class MemberRemoved:
    project_id: UUID
    removed_user_id: UUID
    project_owner_id: UUID
    actor_id: UUID
    reassigned_task_count: int
    affected_user_ids: tuple[UUID, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class TaskCreated:
    task_id: UUID
    project_id: UUID
    actor_id: UUID
    affected_user_ids: tuple[UUID, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class TaskAssigned:
    task_id: UUID
    project_id: UUID
    assignee_id: UUID
    actor_id: UUID
    affected_user_ids: tuple[UUID, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class TaskStatusChanged:
    task_id: UUID
    project_id: UUID
    old_status: str
    new_status: str
    actor_id: UUID
    affected_user_ids: tuple[UUID, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class TaskCompleted:
    task_id: UUID
    project_id: UUID
    actor_id: UUID
    affected_user_ids: tuple[UUID, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class TaskUpdated:
    task_id: UUID
    project_id: UUID
    actor_id: UUID
    affected_user_ids: tuple[UUID, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class TaskDeleted:
    task_id: UUID
    project_id: UUID
    actor_id: UUID
    affected_user_ids: tuple[UUID, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class AttachmentUploaded:
    attachment_id: UUID
    task_id: UUID
    project_id: UUID
    actor_id: UUID


@dataclass(frozen=True)
class AttachmentDeleted:
    attachment_id: UUID
    task_id: UUID
    project_id: UUID
    actor_id: UUID


@dataclass(frozen=True)
class UserLoggedIn:
    user_id: UUID
    ip_address: str | None


@dataclass(frozen=True)
class UserLoggedOut:
    user_id: UUID


@dataclass(frozen=True)
class TokenReuseDetected:
    user_id: UUID
    family_id: UUID
    ip_address: str | None
