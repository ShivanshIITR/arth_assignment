def member_added(*, recipient_name: str, project_name: str) -> tuple[str, str]:
    subject = f"You've been added to {project_name}"
    body = (
        f"Hi {recipient_name},\n\n"
        f'You have been added to the project "{project_name}".\n'
    )
    return subject, body


def task_assigned(
    *, recipient_name: str, task_title: str, project_name: str
) -> tuple[str, str]:
    subject = f"A task was assigned to you in {project_name}"
    body = (
        f"Hi {recipient_name},\n\n"
        f'The task "{task_title}" in project "{project_name}" was assigned to you.\n'
    )
    return subject, body


def task_completed(
    *, recipient_name: str, task_title: str, project_name: str
) -> tuple[str, str]:
    subject = f"A task was completed in {project_name}"
    body = (
        f"Hi {recipient_name},\n\n"
        f'The task "{task_title}" in project "{project_name}" was marked completed.\n'
    )
    return subject, body
