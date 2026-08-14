from pydantic import BaseModel, Field


class DashboardStats(BaseModel):
    total_projects: int
    active_projects: int
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    tasks_by_status: dict[str, int] = Field(
        description="Counts keyed by task status: todo, in_progress, completed"
    )
