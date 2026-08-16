from app.events.dispatcher import EventDispatcher


def register_all_handlers(_dispatcher: EventDispatcher) -> None:
    """Subscribe feature handlers. Phase 0 has no subscribers yet."""
