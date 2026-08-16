from app.models.attachment import Attachment
from app.repositories.attachment_repository import AttachmentRepository
from tests.test_factories import make_project, make_task, make_user


async def test_attachment_repository_create_and_list(db_session) -> None:
    owner = make_user(email="owner@example.com")
    db_session.add(owner)
    await db_session.flush()
    project = make_project(owner)
    db_session.add(project)
    await db_session.flush()
    task = make_task(project, creator=owner)
    db_session.add(task)
    await db_session.flush()

    repo = AttachmentRepository(db_session)
    created = await repo.add(
        Attachment(
            task_id=task.id,
            uploaded_by=owner.id,
            original_filename="spec.pdf",
            storage_path="/tmp/spec.pdf",
            content_type="application/pdf",
            size_bytes=12,
        )
    )
    items = await repo.list_for_task(task.id)
    assert [item.id for item in items] == [created.id]
    loaded = await repo.get_by_id(created.id)
    assert loaded is not None
    assert loaded.original_filename == "spec.pdf"
    await repo.delete(loaded)
    assert await repo.list_for_task(task.id) == []
