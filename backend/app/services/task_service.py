from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.enums import TaskPriority, TaskStatus
from app.models.task import Task
from app.models.user import User
from app.policies.engine import PolicyEngine
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.common import PaginationParams
from app.schemas.task import TaskCreate, TaskUpdate


class TaskService:
    def __init__(
        self,
        session: AsyncSession,
        tasks: TaskRepository,
        projects: ProjectRepository,
        policies: PolicyEngine,
    ) -> None:
        self.session = session
        self.tasks = tasks
        self.projects = projects
        self.policies = policies

    async def create(self, user: User, project_id: UUID, data: TaskCreate) -> Task:
        project = await self._project_or_404(project_id)
        self.policies.authorize(user, "task:create", project)
        if data.assignee_id is not None and data.assignee_id not in project.member_ids:
            raise ValidationError("Assignee must be a project member")
        if data.status == TaskStatus.COMPLETED:
            raise ValidationError("A new task cannot be created as completed")

        task = Task(
            project_id=project.id,
            title=data.title.strip(),
            description=data.description,
            status=data.status,
            priority=data.priority,
            assignee_id=data.assignee_id,
            creator_id=user.id,
            due_date=data.due_date,
        )
        await self.tasks.add(task)
        loaded = await self.tasks.get_by_id(task.id)
        assert loaded is not None
        return loaded

    async def list_for_project(
        self,
        user: User,
        project_id: UUID,
        params: PaginationParams,
        *,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        search: str | None = None,
    ) -> tuple[list[Task], int]:
        project = await self._project_or_404(project_id)
        self.policies.authorize(user, "project:view", project)
        return await self.tasks.list_filtered(
            project.id,
            params,
            status=status,
            priority=priority,
            search=search,
        )

    async def get(self, user: User, task_id: UUID) -> Task:
        task = await self._task_or_404(task_id)
        self.policies.authorize(user, "project:view", task.project)
        return task

    async def update(self, user: User, task_id: UUID, data: TaskUpdate) -> Task:
        task = await self._task_or_404(task_id)
        self.policies.authorize(user, "task:update", task)

        if "assignee_id" in data.model_fields_set and data.assignee_id is not None:
            if data.assignee_id not in task.project.member_ids:
                raise ValidationError("Assignee must be a project member")

        completing = (
            data.status == TaskStatus.COMPLETED and task.status != TaskStatus.COMPLETED
        )
        self._apply_update(task, data)
        if completing:
            self.policies.authorize(user, "task:complete", task)

        await self.session.flush()
        loaded = await self.tasks.get_by_id(task.id)
        assert loaded is not None
        return loaded

    async def delete(self, user: User, task_id: UUID) -> None:
        task = await self._task_or_404(task_id)
        self.policies.authorize(user, "task:delete", task)
        deleted_id = await self.tasks.delete_if_todo(task.id)
        if deleted_id is None:
            raise ConflictError(
                "Task can no longer be deleted because its status changed"
            )

    async def _project_or_404(self, project_id: UUID):
        project = await self.projects.get_by_id(project_id)
        if project is None:
            raise NotFoundError("Project not found")
        return project

    async def _task_or_404(self, task_id: UUID) -> Task:
        task = await self.tasks.get_by_id(task_id)
        if task is None:
            raise NotFoundError("Task not found")
        return task

    @staticmethod
    def _apply_update(task: Task, data: TaskUpdate) -> None:
        if data.title is not None:
            task.title = data.title.strip()
        if data.description is not None:
            task.description = data.description
        if data.status is not None:
            task.status = data.status
        if data.priority is not None:
            task.priority = data.priority
        if "assignee_id" in data.model_fields_set:
            task.assignee_id = data.assignee_id
        if "due_date" in data.model_fields_set:
            task.due_date = data.due_date
