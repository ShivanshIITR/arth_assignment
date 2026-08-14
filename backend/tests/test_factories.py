from datetime import UTC, date, datetime
from uuid import uuid4

from app.core.security import hash_password
from app.models.enums import TaskPriority, TaskStatus
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.task import Task
from app.models.user import User


def make_user(**overrides) -> User:
    now = datetime.now(UTC)
    data = {
        "id": uuid4(),
        "email": f"user-{uuid4().hex[:8]}@example.com",
        "hashed_password": hash_password("password123"),
        "full_name": "Test User",
        "created_at": now,
        "updated_at": now,
    }
    data.update(overrides)
    return User(**data)


def make_project(owner: User, members: list[User] | None = None, **overrides) -> Project:
    now = datetime.now(UTC)
    data = {
        "id": uuid4(),
        "name": "Test Project",
        "description": "A project",
        "owner_id": owner.id,
        "created_at": now,
        "updated_at": now,
    }
    data.update(overrides)
    project = Project(**data)
    project.owner = owner
    member_users = list(members) if members is not None else [owner]
    if owner not in member_users:
        member_users.insert(0, owner)
    project.members = [
        ProjectMember(project_id=project.id, user_id=user.id, user=user, project=project)
        for user in member_users
    ]
    return project


def make_task(
    project: Project,
    creator: User,
    assignee: User | None = None,
    **overrides,
) -> Task:
    now = datetime.now(UTC)
    data = {
        "id": uuid4(),
        "project_id": project.id,
        "title": "Test Task",
        "description": "A task",
        "status": TaskStatus.TODO,
        "priority": TaskPriority.MEDIUM,
        "assignee_id": assignee.id if assignee is not None else None,
        "creator_id": creator.id,
        "due_date": date(2026, 12, 31),
        "created_at": now,
        "updated_at": now,
    }
    data.update(overrides)
    task = Task(**data)
    task.project = project
    task.creator = creator
    task.assignee = assignee
    return task
