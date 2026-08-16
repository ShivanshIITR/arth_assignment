from sqlalchemy import select

from app.models.audit_log import AuditLog
from app.models.enums import AuditEventType
from tests.conftest import register_user


async def test_login_writes_audit_row_with_ip(client, db_session) -> None:
    await register_user(client, email="ada@example.com")
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "ada@example.com", "password": "password123"},
    )
    assert response.status_code == 200

    result = await db_session.execute(
        select(AuditLog).where(AuditLog.event_type == AuditEventType.LOGIN)
    )
    entry = result.scalar_one()
    assert entry.ip_address is not None
    assert entry.actor_id is not None
