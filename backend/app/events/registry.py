from app.events.dispatcher import EventDispatcher
from app.events.events import (
    AttachmentDeleted,
    AttachmentUploaded,
    MemberAdded,
    MemberRemoved,
    ProjectCreated,
    ProjectUpdated,
    TaskAssigned,
    TaskCreated,
    TaskDeleted,
    TaskStatusChanged,
    TaskUpdated,
)
from app.events.handlers.activity_handler import ActivityHandler


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
