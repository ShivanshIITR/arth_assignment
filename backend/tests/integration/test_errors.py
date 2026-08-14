async def test_validation_errors_use_error_envelope(client) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email", "password": "short", "full_name": ""},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["message"] == "Request validation failed"
    assert "details" in body["error"]


async def test_request_id_header_is_echoed(client) -> None:
    response = await client.get("/health", headers={"X-Request-ID": "test-request-1"})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "test-request-1"


async def test_unknown_route_uses_error_envelope(client) -> None:
    response = await client.get("/no-such-route")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
