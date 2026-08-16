from pathlib import Path

import pytest

from app.core.storage.local_storage import LocalFilesystemStorage
from app.main import create_app
from tests.conftest import auth_client_headers

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


@pytest.fixture
def app(tmp_path: Path):
    application = create_app()
    application.state.redis = None
    application.state.arq_pool = None
    application.state.storage = LocalFilesystemStorage(tmp_path)
    return application


async def _task(client, headers: dict[str, str]) -> str:
    project = await client.post(
        "/api/v1/projects", headers=headers, json={"name": "Files"}
    )
    task = await client.post(
        f"/api/v1/projects/{project.json()['id']}/tasks",
        headers=headers,
        json={"title": "Has files"},
    )
    return task.json()["id"]


async def test_upload_download_delete_round_trip(client) -> None:
    _owner, headers = await auth_client_headers(client, "owner@example.com")
    task_id = await _task(client, headers)
    uploaded = await client.post(
        f"/api/v1/tasks/{task_id}/attachments",
        headers=headers,
        files={"file": ("shot.png", PNG, "image/png")},
    )
    assert uploaded.status_code == 201, uploaded.text
    attachment_id = uploaded.json()["id"]
    assert uploaded.json()["original_filename"] == "shot.png"

    listed = await client.get(
        f"/api/v1/tasks/{task_id}/attachments", headers=headers
    )
    assert listed.status_code == 200
    assert listed.json()["items"][0]["id"] == attachment_id

    downloaded = await client.get(
        f"/api/v1/attachments/{attachment_id}/download", headers=headers
    )
    assert downloaded.status_code == 200
    assert downloaded.content == PNG

    deleted = await client.delete(
        f"/api/v1/attachments/{attachment_id}", headers=headers
    )
    assert deleted.status_code == 204
    missing = await client.get(
        f"/api/v1/attachments/{attachment_id}/download", headers=headers
    )
    assert missing.status_code == 404


async def test_non_member_cannot_use_attachments(client) -> None:
    _owner, owner_headers = await auth_client_headers(client, "owner@example.com")
    _outsider, outsider_headers = await auth_client_headers(
        client, "out@example.com"
    )
    task_id = await _task(client, owner_headers)
    uploaded = await client.post(
        f"/api/v1/tasks/{task_id}/attachments",
        headers=owner_headers,
        files={"file": ("shot.png", PNG, "image/png")},
    )
    attachment_id = uploaded.json()["id"]

    assert (
        await client.post(
            f"/api/v1/tasks/{task_id}/attachments",
            headers=outsider_headers,
            files={"file": ("shot.png", PNG, "image/png")},
        )
    ).status_code == 403
    assert (
        await client.get(
            f"/api/v1/tasks/{task_id}/attachments", headers=outsider_headers
        )
    ).status_code == 403
    assert (
        await client.get(
            f"/api/v1/attachments/{attachment_id}/download",
            headers=outsider_headers,
        )
    ).status_code == 403
    assert (
        await client.delete(
            f"/api/v1/attachments/{attachment_id}", headers=outsider_headers
        )
    ).status_code == 403


async def test_oversized_upload_is_rejected(client) -> None:
    from app.core.config import get_settings

    _owner, headers = await auth_client_headers(client, "owner@example.com")
    task_id = await _task(client, headers)
    huge = PNG + b"x" * (2 * 1024 * 1024)
    original = get_settings().max_attachment_size_mb
    get_settings().max_attachment_size_mb = 1
    try:
        response = await client.post(
            f"/api/v1/tasks/{task_id}/attachments",
            headers=headers,
            files={"file": ("big.png", huge, "image/png")},
        )
        assert response.status_code == 413
    finally:
        get_settings().max_attachment_size_mb = original
