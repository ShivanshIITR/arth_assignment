from dataclasses import dataclass, field


@dataclass(frozen=True)
class PolicyRule:
    name: str
    description: str | None = None
    all_of: tuple[str, ...] = field(default_factory=tuple)
    any_of: tuple[str, ...] = field(default_factory=tuple)
