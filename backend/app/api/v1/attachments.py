from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    CurrentUser,
    EventDispatcherDep,
    PolicyEngineDep,
    SettingsDep,
    StorageDep,
    get_db,
)
from app.repositories.attachment_repository import AttachmentRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.attachment import AttachmentList, AttachmentRead
from app.services.attachment_service import AttachmentService

nested_router = APIRouter(
    prefix="/tasks/{task_id}/attachments", tags=["attachments"]
)
router = APIRouter(prefix="/attachments", tags=["attachments"])


def get_attachment_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    policies: PolicyEngineDep,
    dispatcher: EventDispatcherDep,
    storage: StorageDep,
    settings: SettingsDep,
) -> AttachmentService:
    return AttachmentService(
        session=session,
        attachments=AttachmentRepository(session),
        tasks=TaskRepository(session),
        policies=policies,
        dispatcher=dispatcher,
        storage=storage,
        settings=settings,
    )


AttachmentServiceDep = Annotated[
    AttachmentService, Depends(get_attachment_service)
]


@nested_router.post(
    "", response_model=AttachmentRead, status_code=status.HTTP_201_CREATED
)
async def upload_attachment(
    task_id: UUID,
    file: UploadFile,
    current_user: CurrentUser,
    service: AttachmentServiceDep,
) -> AttachmentRead:
    async def chunks():
        while True:
            data = await file.read(64 * 1024)
            if not data:
                break
            yield data

    attachment = await service.upload(
        current_user,
        task_id,
        filename=file.filename or "upload",
        chunks=chunks(),
    )
    return AttachmentRead.model_validate(attachment)


@nested_router.get("", response_model=AttachmentList)
async def list_attachments(
    task_id: UUID,
    current_user: CurrentUser,
    service: AttachmentServiceDep,
) -> AttachmentList:
    items = await service.list_for_task(current_user, task_id)
    return AttachmentList(
        items=[AttachmentRead.model_validate(item) for item in items]
    )


@router.get("/{attachment_id}/download")
async def download_attachment(
    attachment_id: UUID,
    current_user: CurrentUser,
    service: AttachmentServiceDep,
) -> StreamingResponse:
    attachment = await service.get_for_download(current_user, attachment_id)
    filename = attachment.original_filename.replace('"', "")
    return StreamingResponse(
        service.storage.stream(attachment.storage_path),
        media_type=attachment.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(
    attachment_id: UUID,
    current_user: CurrentUser,
    service: AttachmentServiceDep,
) -> None:
    await service.delete(current_user, attachment_id)
