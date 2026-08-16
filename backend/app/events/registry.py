from collections.abc import Callable

from arq.connections import ArqRedis
from redis.asyncio import Redis

from app.events.dispatcher import EventDispatcher
from app.events.events import (
    AttachmentDeleted,
    AttachmentUploaded,
    MemberAdded,
    MemberRemoved,
    ProjectCreated,
    ProjectDeleted,
    ProjectUpdated,
    TaskAssigned,
    TaskCompleted,
    TaskCreated,
    TaskDeleted,
    TaskStatusChanged,
    TaskUpdated,
    TokenReuseDetected,
    UserLoggedIn,
    UserLoggedOut,
)
from app.events.handlers.activity_handler import ActivityHandler
from app.events.handlers.audit_handler import AuditHandler
from app.events.handlers.cache_invalidation_handler import CacheInvalidationHandler
from app.events.handlers.notification_handler import NotificationHandler
from app.events.handlers.websocket_handler import WebSocketHandler
from app.websocket.connection_manager import ConnectionManager


def register_all_handlers(dispatcher: EventDispatcher) -> None:
    activity = ActivityHandler()
    dispatcher.subscribe(ProjectCreated, activity.on_project_created)
    dispatcher.subscribe(ProjectUpdated, activity.on_project_updated)
    dispatcher.subscribe(MemberAdded, activity.on_member_added)
    dispatcher.subscribe(MemberRemoved, activity.on_member_removed)
    dispatcher.subscribe(TaskCreated, activity.on_task_created)
    dispatcher.subscribe(TaskAssigned, activity.on_task_assigned)
    dispatcher.subscribe(TaskStatusChanged, activity.on_task_status_changed)
    dispatcher.subscribe(TaskUpdated, activity.on_task_updated)
    dispatcher.subscribe(TaskDeleted, activity.on_task_deleted)
    dispatcher.subscribe(AttachmentUploaded, activity.on_attachment_uploaded)
    dispatcher.subscribe(AttachmentDeleted, activity.on_attachment_deleted)

    audit = AuditHandler()
    dispatcher.subscribe(UserLoggedIn, audit.on_user_logged_in)
    dispatcher.subscribe(UserLoggedOut, audit.on_user_logged_out)
    dispatcher.subscribe(TokenReuseDetected, audit.on_token_reuse_detected)
    dispatcher.subscribe(ProjectCreated, audit.on_project_created)
    dispatcher.subscribe(ProjectUpdated, audit.on_project_updated)
    dispatcher.subscribe(ProjectDeleted, audit.on_project_deleted)
    dispatcher.subscribe(MemberAdded, audit.on_member_added)
    dispatcher.subscribe(MemberRemoved, audit.on_member_removed)
    dispatcher.subscribe(TaskDeleted, audit.on_task_deleted)
    dispatcher.subscribe(TaskCompleted, audit.on_task_completed)
    dispatcher.subscribe(AttachmentUploaded, audit.on_attachment_uploaded)
    dispatcher.subscribe(AttachmentDeleted, audit.on_attachment_deleted)


def register_cache_handlers(
    dispatcher: EventDispatcher,
    redis_provider: Callable[[], Redis | None],
) -> None:
    cache = CacheInvalidationHandler(redis_provider)
    dispatcher.subscribe_after_commit(ProjectCreated, cache.on_project_created)
    dispatcher.subscribe_after_commit(ProjectUpdated, cache.on_project_updated)
    dispatcher.subscribe_after_commit(ProjectDeleted, cache.on_project_deleted)
    dispatcher.subscribe_after_commit(MemberAdded, cache.on_member_changed)
    dispatcher.subscribe_after_commit(MemberRemoved, cache.on_member_changed)
    dispatcher.subscribe_after_commit(TaskCreated, cache.on_task_changed)
    dispatcher.subscribe_after_commit(TaskUpdated, cache.on_task_changed)
    dispatcher.subscribe_after_commit(TaskStatusChanged, cache.on_task_changed)
    dispatcher.subscribe_after_commit(TaskDeleted, cache.on_task_changed)


def register_notification_handlers(
    dispatcher: EventDispatcher,
    pool_provider: Callable[[], ArqRedis | None],
) -> None:
    notifications = NotificationHandler(pool_provider)
    dispatcher.subscribe_after_commit(MemberAdded, notifications.on_member_added)
    dispatcher.subscribe_after_commit(TaskAssigned, notifications.on_task_assigned)
    dispatcher.subscribe_after_commit(TaskCompleted, notifications.on_task_completed)


def register_websocket_handlers(
    dispatcher: EventDispatcher,
    manager_provider: Callable[[], ConnectionManager],
) -> None:
    handler = WebSocketHandler(manager_provider)
    dispatcher.subscribe_after_commit(TaskCreated, handler.on_task_created)
    dispatcher.subscribe_after_commit(TaskUpdated, handler.on_task_updated)
    dispatcher.subscribe_after_commit(
        TaskStatusChanged, handler.on_task_status_changed
    )
    dispatcher.subscribe_after_commit(TaskDeleted, handler.on_task_deleted)
    dispatcher.subscribe_after_commit(TaskAssigned, handler.on_task_assigned)
    dispatcher.subscribe_after_commit(MemberRemoved, handler.on_member_removed)
