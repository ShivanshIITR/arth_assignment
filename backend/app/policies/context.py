from dataclasses import dataclass
from typing import Any

from app.models.user import User


@dataclass
class PolicyContext:
    user: User
    action: str
    resource: Any
