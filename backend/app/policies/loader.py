from pathlib import Path

import yaml

from app.policies.predicates import PREDICATE_REGISTRY
from app.policies.rules import PolicyRule

DEFAULT_POLICY_PATH = Path(__file__).with_name("policies.yaml")


class PolicyConfigError(ValueError):
    """Raised when policies.yaml is missing, malformed, or references unknown predicates."""


def load_policy_rules(path: Path | None = None) -> dict[str, PolicyRule]:
    policy_path = path or DEFAULT_POLICY_PATH
    try:
        raw = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PolicyConfigError(f"Policy file not found: {policy_path}") from exc
    except yaml.YAMLError as exc:
        raise PolicyConfigError(f"Invalid YAML in {policy_path}") from exc

    if not isinstance(raw, dict) or "policies" not in raw or not isinstance(raw["policies"], dict):
        raise PolicyConfigError("Policy file must contain a top-level 'policies' mapping")

    rules: dict[str, PolicyRule] = {}
    for name, spec in raw["policies"].items():
        if not isinstance(spec, dict):
            raise PolicyConfigError(f"Policy '{name}' must be a mapping")

        all_of = tuple(spec.get("all_of") or ())
        any_of = tuple(spec.get("any_of") or ())
        if not all_of and not any_of:
            raise PolicyConfigError(f"Policy '{name}' must declare all_of and/or any_of")

        unknown = [item for item in (*all_of, *any_of) if item not in PREDICATE_REGISTRY]
        if unknown:
            raise PolicyConfigError(
                f"Policy '{name}' references unknown predicates: {', '.join(unknown)}"
            )

        rules[name] = PolicyRule(
            name=name,
            description=spec.get("description"),
            all_of=all_of,
            any_of=any_of,
        )
    return rules
