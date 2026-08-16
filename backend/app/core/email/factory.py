from app.core.config import Settings
from app.core.email.console_provider import ConsoleEmailProvider
from app.core.email.provider import EmailProvider
from app.core.email.smtp_provider import SMTPEmailProvider


def get_email_provider(settings: Settings) -> EmailProvider:
    if settings.email_backend.lower() == "smtp":
        return SMTPEmailProvider(settings)
    return ConsoleEmailProvider()
