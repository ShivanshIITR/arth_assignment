from app.models.audit_log import AuditLog
from app.models.enums import AuditEventType
from app.repositories.audit_repository import AuditRepository
from app.schemas.common import PaginationParams
from tests.test_factories import make_project, make_user


async def test_audit_repository_create_and_list(db_session) -> None:
    owner = make_user(email="owner@example.com")
    other = make_user(email="other@example.com")
    db_session.add_all([owner, other])
    await db_session.flush()
    project = make_project(owner)
    db_session.add(project)
    await db_session.flush()

    repo = AuditRepository(db_session)
    await repo.create(
        AuditLog(
            actor_id=owner.id,
            event_type=AuditEventType.PROJECT_CREATED,
            project_id=project.id,
            resource_type="project",
            resource_id=project.id,
            ip_address="127.0.0.1",
        )
    )
    await repo.create(
        AuditLog(
            actor_id=other.id,
            event_type=AuditEventType.LOGIN,
            ip_address="10.0.0.1",
        )
    )

    project_items, project_total = await repo.list_for_project(
        project.id, PaginationParams()
    )
    assert project_total == 1
    assert project_items[0].event_type == AuditEventType.PROJECT_CREATED

    user_items, user_total = await repo.list_for_user(other.id, PaginationParams())
    assert user_total == 1
    assert user_items[0].event_type == AuditEventType.LOGIN
    assert str(user_items[0].ip_address) == "10.0.0.1"
