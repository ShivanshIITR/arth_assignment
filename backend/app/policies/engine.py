from app.core.exceptions import ForbiddenError
from app.models.user import User
from app.policies.context import PolicyContext
from app.policies.loader import load_policy_rules
from app.policies.predicates import PREDICATE_REGISTRY
from app.policies.rules import PolicyRule


class PolicyEngine:
    def __init__(self, rules: dict[str, PolicyRule] | None = None) -> None:
        self.rules = rules if rules is not None else load_policy_rules()
        self.predicates = PREDICATE_REGISTRY

    def check(self, user: User, action: str, resource: object) -> bool:
        rule = self.rules.get(action)
        if rule is None:
            return False

        ctx = PolicyContext(user=user, action=action, resource=resource)

        if rule.all_of and not all(self.predicates[name](ctx) for name in rule.all_of):
            return False
        if rule.any_of and not any(self.predicates[name](ctx) for name in rule.any_of):
            return False
        return True

    def authorize(self, user: User, action: str, resource: object) -> None:
        if not self.check(user, action, resource):
            raise ForbiddenError(f"Not allowed to perform {action}")


def load_policy_engine() -> PolicyEngine:
    return PolicyEngine(load_policy_rules())
