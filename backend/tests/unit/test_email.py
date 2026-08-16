from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.core.email.console_provider import ConsoleEmailProvider
from app.core.email.factory import get_email_provider
from app.core.email.smtp_provider import SMTPEmailProvider
from app.jobs import email_templates
from app.jobs.tasks import send_email_job
from tests.test_factories import make_project, make_task, make_user


def test_member_added_template_includes_project_name() -> None:
    subject, body = email_templates.member_added(
        recipient_name="Ada", project_name="Apollo"
    )
    assert "Apollo" in subject
    assert "Ada" in body
    assert "Apollo" in body


def test_task_assigned_template_includes_task_title() -> None:
    subject, body = email_templates.task_assigned(
        recipient_name="Ada", task_title="Write tests", project_name="Apollo"
    )
    assert "Apollo" in subject
    assert "Write tests" in body


def test_task_completed_template_includes_task_title() -> None:
    subject, body = email_templates.task_completed(
        recipient_name="Ada", task_title="Write tests", project_name="Apollo"
    )
    assert "completed" in subject.lower()
    assert "Write tests" in body


def test_factory_defaults_to_console() -> None:
    provider = get_email_provider(Settings(email_backend="console"))
    assert isinstance(provider, ConsoleEmailProvider)


def test_factory_selects_smtp() -> None:
    provider = get_email_provider(Settings(email_backend="smtp"))
    assert isinstance(provider, SMTPEmailProvider)


@pytest.mark.asyncio
async def test_send_email_job_member_added_uses_provider(db_session) -> None:
    owner = make_user(email="owner@example.com", full_name="Owner")
    member = make_user(email="member@example.com", full_name="Member")
    db_session.add_all([owner, member])
    await db_session.flush()
    project = make_project(owner)
    db_session.add(project)
    await db_session.flush()

    spy = SimpleNamespace(send=AsyncMock())

    @asynccontextmanager
    async def session_factory():
        yield db_session

    await send_email_job(
        {"email_provider": spy, "session_factory": session_factory},
        "member_added",
        str(member.id),
        str(project.id),
    )
    spy.send.assert_awaited_once()
    to, subject, body = spy.send.await_args.args
    assert to == "member@example.com"
    assert project.name in subject
    assert "Member" in body


@pytest.mark.asyncio
async def test_send_email_job_task_assigned_uses_provider(db_session) -> None:
    owner = make_user(email="owner@example.com", full_name="Owner")
    member = make_user(email="member@example.com", full_name="Member")
    db_session.add_all([owner, member])
    await db_session.flush()
    project = make_project(owner, members=[owner, member])
    db_session.add(project)
    await db_session.flush()
    task = make_task(project, creator=owner, assignee=member, title="Ship it")
    db_session.add(task)
    await db_session.flush()

    spy = SimpleNamespace(send=AsyncMock())

    @asynccontextmanager
    async def session_factory():
        yield db_session

    await send_email_job(
        {"email_provider": spy, "session_factory": session_factory},
        "task_assigned",
        str(member.id),
        str(task.id),
    )
    spy.send.assert_awaited_once()
    to, subject, body = spy.send.await_args.args
    assert to == "member@example.com"
    assert "Ship it" in body


@pytest.mark.asyncio
async def test_send_email_job_skips_unknown_recipient(db_session) -> None:
    spy = SimpleNamespace(send=AsyncMock())

    @asynccontextmanager
    async def session_factory():
        yield db_session

    await send_email_job(
        {"email_provider": spy, "session_factory": session_factory},
        "member_added",
        str(uuid4()),
        str(uuid4()),
    )
    spy.send.assert_not_awaited()
