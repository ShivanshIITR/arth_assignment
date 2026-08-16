from app.models.activity_log import ActivityLog
from app.models.enums import ActivityEventType
from app.repositories.activity_repository import ActivityRepository
from app.schemas.common import PaginationParams
from tests.test_factories import make_project, make_user


async def test_activity_repository_create_and_list(db_session) -> None:
    owner = make_user(email="owner@example.com")
    db_session.add(owner)
    await db_session.flush()
    project = make_project(owner)
    db_session.add(project)
    await db_session.flush()

    repo = ActivityRepository(db_session)
    first = await repo.create(
        ActivityLog(
            project_id=project.id,
            actor_id=owner.id,
            event_type=ActivityEventType.PROJECT_CREATED,
            event_metadata={"name": project.name},
        )
    )
    second = await repo.create(
        ActivityLog(
            project_id=project.id,
            actor_id=owner.id,
            event_type=ActivityEventType.PROJECT_UPDATED,
        )
    )

    items, total = await repo.list_for_project(
        project.id, PaginationParams(page=1, page_size=20)
    )
    assert total == 2
    assert [entry.id for entry in items] == [second.id, first.id]
    assert items[0].event_type == ActivityEventType.PROJECT_UPDATED
    assert items[1].event_metadata == {"name": project.name}
