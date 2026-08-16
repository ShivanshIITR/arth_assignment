async def health_job(ctx: dict) -> str:
    """Minimal job used to verify the worker can dequeue and run work."""
    return "ok"
