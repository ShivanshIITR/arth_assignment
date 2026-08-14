from datetime import date

import pytest
import yaml

from app.core.exceptions import ForbiddenError
from app.models.enums import TaskPriority, TaskStatus
from app.policies.context import PolicyContext
from app.policies.engine import PolicyEngine
from app.policies.loader import PolicyConfigError, load_policy_rules
from app.policies.predicates import (
    is_project_member,
    is_project_owner,
    is_task_assignee,
    is_task_creator,
    task_has_assignee,
    task_required_fields_complete,
    task_status_is_todo,
)
from tests.test_factories import make_project, make_task, make_user


@pytest.fixture
def engine() -> PolicyEngine:
    return PolicyEngine()


@pytest.fixture
def owner():
    return make_user(email="owner@example.com", full_name="Owner")


@pytest.fixture
def member():
    return make_user(email="member@example.com", full_name="Member")


@pytest.fixture
def outsider():
    return make_user(email="outsider@example.com", full_name="Outsider")


@pytest.fixture
def project(owner, member):
    return make_project(owner, members=[owner, member])


def _ctx(user, action, resource) -> PolicyContext:
    return PolicyContext(user=user, action=action, resource=resource)


def test_is_project_owner(owner, member, project) -> None:
    assert is_project_owner(_ctx(owner, "project:update", project)) is True
    assert is_project_owner(_ctx(member, "project:update", project)) is False


def test_is_project_member(owner, member, outsider, project) -> None:
    assert is_project_member(_ctx(owner, "project:view", project)) is True
    assert is_project_member(_ctx(member, "project:view", project)) is True
    assert is_project_member(_ctx(outsider, "project:view", project)) is False


def test_task_predicates(owner, member, project) -> None:
    task = make_task(project, creator=member, assignee=owner)
    assert is_task_creator(_ctx(member, "task:update", task)) is True
    assert is_task_creator(_ctx(owner, "task:update", task)) is False
    assert is_task_assignee(_ctx(owner, "task:update", task)) is True
    assert is_task_assignee(_ctx(member, "task:update", task)) is False
    assert task_status_is_todo(_ctx(owner, "task:delete", task)) is True
    assert task_has_assignee(_ctx(owner, "task:complete", task)) is True
    assert task_required_fields_complete(_ctx(owner, "task:complete", task)) is True


def test_task_required_fields_incomplete_without_due_date(member, project) -> None:
    task = make_task(project, creator=member, assignee=member, due_date=None)
    assert task_required_fields_complete(_ctx(member, "task:complete", task)) is False


def test_project_view_allows_members_only(
    engine, owner, member, outsider, project
) -> None:
    engine.authorize(owner, "project:view", project)
    engine.authorize(member, "project:view", project)
    with pytest.raises(ForbiddenError):
        engine.authorize(outsider, "project:view", project)


def test_project_update_and_delete_owner_only(engine, owner, member, project) -> None:
    engine.authorize(owner, "project:update", project)
    engine.authorize(owner, "project:delete", project)
    with pytest.raises(ForbiddenError):
        engine.authorize(member, "project:update", project)
    with pytest.raises(ForbiddenError):
        engine.authorize(member, "project:delete", project)


def test_task_create_requires_membership(engine, member, outsider, project) -> None:
    engine.authorize(member, "task:create", project)
    with pytest.raises(ForbiddenError):
        engine.authorize(outsider, "task:create", project)


def test_task_update_creator_assignee_or_owner(
    engine, owner, member, outsider, project
) -> None:
    task = make_task(project, creator=member, assignee=member)
    engine.authorize(member, "task:update", task)
    engine.authorize(owner, "task:update", task)
    with pytest.raises(ForbiddenError):
        engine.authorize(outsider, "task:update", task)


def test_task_delete_requires_todo_and_owner(engine, owner, member, project) -> None:
    todo = make_task(project, creator=member, status=TaskStatus.TODO)
    in_progress = make_task(project, creator=member, status=TaskStatus.IN_PROGRESS)
    engine.authorize(owner, "task:delete", todo)
    with pytest.raises(ForbiddenError):
        engine.authorize(member, "task:delete", todo)
    with pytest.raises(ForbiddenError):
        engine.authorize(owner, "task:delete", in_progress)


def test_task_complete_requires_assignee_and_fields(engine, member, project) -> None:
    complete = make_task(
        project,
        creator=member,
        assignee=member,
        title="Ship it",
        priority=TaskPriority.HIGH,
        due_date=date(2026, 9, 1),
    )
    missing_assignee = make_task(project, creator=member, assignee=None)
    engine.authorize(member, "task:complete", complete)
    with pytest.raises(ForbiddenError):
        engine.authorize(member, "task:complete", missing_assignee)


def test_unknown_action_is_denied(engine, owner, project) -> None:
    assert engine.check(owner, "project:explode", project) is False
    with pytest.raises(ForbiddenError):
        engine.authorize(owner, "project:explode", project)


def test_loader_rejects_unknown_predicates(tmp_path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text(
        yaml.dump({"policies": {"project:view": {"all_of": ["not_a_real_predicate"]}}}),
        encoding="utf-8",
    )
    with pytest.raises(PolicyConfigError, match="unknown predicates"):
        load_policy_rules(path)


def test_loader_rejects_empty_rule(tmp_path) -> None:
    path = tmp_path / "empty.yaml"
    path.write_text(
        yaml.dump({"policies": {"project:view": {"description": "nope"}}}),
        encoding="utf-8",
    )
    with pytest.raises(PolicyConfigError, match="all_of and/or any_of"):
        load_policy_rules(path)
