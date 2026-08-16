from collections.abc import Callable

from app.models.enums import TaskStatus
from app.models.project import Project
from app.models.task import Task
from app.policies.context import PolicyContext

Predicate = Callable[[PolicyContext], bool]


def _project_of(resource: object) -> object:
    """Resolve the Project a predicate should reason about.

    `task:create` authorizes against the parent Project because no Task
    row exists yet; other task actions authorize against a Task that
    already has its project relationship loaded. Duck-typed objects with
    `owner_id` / `member_ids` (e.g. cached project views) also work.
    """
    if isinstance(resource, Task):
        return resource.project
    return resource


def is_project_owner(ctx: PolicyContext) -> bool:
    return _project_of(ctx.resource).owner_id == ctx.user.id


def is_project_member(ctx: PolicyContext) -> bool:
    return ctx.user.id in _project_of(ctx.resource).member_ids


def is_task_creator(ctx: PolicyContext) -> bool:
    return ctx.resource.creator_id == ctx.user.id


def is_task_assignee(ctx: PolicyContext) -> bool:
    return ctx.resource.assignee_id == ctx.user.id


def task_status_is_todo(ctx: PolicyContext) -> bool:
    return ctx.resource.status == TaskStatus.TODO


def task_has_assignee(ctx: PolicyContext) -> bool:
    return ctx.resource.assignee_id is not None


def task_required_fields_complete(ctx: PolicyContext) -> bool:
    task = ctx.resource
    return all([task.title, task.assignee_id, task.priority, task.due_date])


PREDICATE_REGISTRY: dict[str, Predicate] = {
    "is_project_owner": is_project_owner,
    "is_project_member": is_project_member,
    "is_task_creator": is_task_creator,
    "is_task_assignee": is_task_assignee,
    "task_status_is_todo": task_status_is_todo,
    "task_has_assignee": task_has_assignee,
    "task_required_fields_complete": task_required_fields_complete,
}
