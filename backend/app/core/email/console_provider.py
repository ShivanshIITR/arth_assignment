import structlog

logger = structlog.get_logger("app.email")


class ConsoleEmailProvider:
    """Logs messages instead of delivering them — default for tests and local CI."""

    async def send(self, to: str, subject: str, body: str) -> None:
        logger.info("email_console", to=to, subject=subject, body=body)
