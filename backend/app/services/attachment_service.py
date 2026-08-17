import asyncio
from collections.abc import AsyncIterator
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import NotFoundError, PayloadTooLargeError, ValidationError
from app.core.storage.base import StorageBackend
from app.core.storage.validation import detect_content_type, sanitize_filename
from app.events.dispatcher import EventDispatcher
from app.events.events import AttachmentDeleted, AttachmentUploaded
from app.models.attachment import Attachment
from app.models.user import User
from app.policies.engine import PolicyEngine
from app.repositories.attachment_repository import AttachmentRepository
from app.repositories.task_repository import TaskRepository


class AttachmentService:
    def __init__(
        self,
        session: AsyncSession,
        attachments: AttachmentRepository,
        tasks: TaskRepository,
        policies: PolicyEngine,
        dispatcher: EventDispatcher,
        storage: StorageBackend,
        settings: Settings,
    ) -> None:
        self.session = session
        self.attachments = attachments
        self.tasks = tasks
        self.policies = policies
        self.dispatcher = dispatcher
        self.storage = storage
        self.settings = settings

    async def list_for_task(self, user: User, task_id: UUID) -> list[Attachment]:
        task = await self._task_or_404(task_id)
        self.policies.authorize(user, "attachment:view", task.project)
        return await self.attachments.list_for_task(task.id)

    async def get_for_download(self, user: User, attachment_id: UUID) -> Attachment:
        attachment = await self._attachment_or_404(attachment_id)
        self.policies.authorize(user, "attachment:view", attachment)
        return attachment

    async def upload(
        self,
        user: User,
        task_id: UUID,
        *,
        filename: str,
        chunks: AsyncIterator[bytes],
    ) -> Attachment:
        task = await self._task_or_404(task_id)
        self.policies.authorize(user, "attachment:create", task.project)
        safe_name = sanitize_filename(filename)
        dest_key = f"{task.id}/{uuid4()}_{safe_name}"
        max_bytes = self.settings.max_attachment_size_mb * 1024 * 1024
        content_type, size_bytes, stored = await self._store(
            chunks, dest_key, safe_name, max_bytes
        )
        attachment = Attachment(
            task_id=task.id,
            uploaded_by=user.id,
            original_filename=safe_name,
            storage_path=stored,
            content_type=content_type,
            size_bytes=size_bytes,
        )
        await self.attachments.add(attachment)
        loaded = await self.attachments.get_by_id(attachment.id)
        assert loaded is not None
        await self.dispatcher.emit(
            AttachmentUploaded(
                attachment_id=loaded.id,
                task_id=loaded.task_id,
                project_id=loaded.task.project_id,
                actor_id=user.id,
            ),
            self.session,
        )
        return loaded

    async def delete(self, user: User, attachment_id: UUID) -> None:
        attachment = await self._attachment_or_404(attachment_id)
        self.policies.authorize(user, "attachment:delete", attachment)
        event = AttachmentDeleted(
            attachment_id=attachment.id,
            task_id=attachment.task_id,
            project_id=attachment.task.project_id,
            actor_id=user.id,
        )
        await self.dispatcher.emit(event, self.session)
        path = attachment.storage_path
        await self.attachments.delete(attachment)
        await self.storage.delete(path)

    async def _store(
        self,
        chunks: AsyncIterator[bytes],
        dest_key: str,
        filename: str,
        max_bytes: int,
    ) -> tuple[str, int, str]:
        first = b""
        async for chunk in chunks:
            first = chunk
            break
        if not first:
            raise ValidationError("Empty file")
        content_type = detect_content_type(first[:64], filename)
        size = 0

        async def limited() -> AsyncIterator[bytes]:
            nonlocal size
            size += len(first)
            if size > max_bytes:
                raise PayloadTooLargeError("File is too large")
            yield first
            async for chunk in chunks:
                size += len(chunk)
                if size > max_bytes:
                    raise PayloadTooLargeError("File is too large")
                yield chunk

        try:
            stored = await self.storage.save(limited(), dest_key)
        except PayloadTooLargeError:
            leftover = Path(self.settings.upload_dir) / dest_key
            await asyncio.to_thread(leftover.unlink, missing_ok=True)
            raise
        return content_type, size, stored

    async def _task_or_404(self, task_id: UUID):
        task = await self.tasks.get_by_id(task_id)
        if task is None:
            raise NotFoundError("Task not found")
        return task

    async def _attachment_or_404(self, attachment_id: UUID) -> Attachment:
        attachment = await self.attachments.get_by_id(attachment_id)
        if attachment is None:
            raise NotFoundError("Attachment not found")
        return attachment
