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
