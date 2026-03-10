from __future__ import annotations


async def test_post_register_success(client):
    payload = {"username": "alice", "password": "password123", "display_name": "Alice"}
    resp = await client.post("/api/v1/auth/register", json=payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["username"] == "alice"
    assert body["user"]["display_name"] == "Alice"
    assert body["access_token"]
    assert body["refresh_token"]


async def test_post_register_duplicate_username_returns_409(client):
    payload = {"username": "alice", "password": "password123", "display_name": "Alice"}
    await client.post("/api/v1/auth/register", json=payload)

    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 409
    body = resp.json()
    assert body["error"] == "conflict"


async def test_post_login_success(client):
    await client.post(
        "/api/v1/auth/register",
        json={"username": "bob", "password": "password123"},
    )

    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "bob", "password": "password123"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["user"]["username"] == "bob"
    assert body["access_token"]
    assert body["refresh_token"]


async def test_post_login_wrong_password_returns_401(client):
    await client.post(
        "/api/v1/auth/register",
        json={"username": "bob", "password": "password123"},
    )

    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "bob", "password": "wrong"},
    )
    assert resp.status_code == 401
    assert resp.json()["error"] == "authentication_error"


async def test_post_login_validation_errors(client):
    resp = await client.post("/api/v1/auth/login", json={"username": "bob"})
    assert resp.status_code == 422


async def test_post_refresh_success(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"username": "carol", "password": "password123"},
    )
    refresh_token = reg.json()["refresh_token"]

    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"]
    assert body["refresh_token"] != refresh_token


async def test_post_refresh_invalid_token_returns_401(client):
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": "not-in-db"})
    assert resp.status_code == 401
    assert resp.json()["error"] == "authentication_error"


async def test_post_logout_success(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"username": "dave", "password": "password123"},
    )
    refresh_token = reg.json()["refresh_token"]

    resp = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
    )
    assert resp.status_code == 204

    resp2 = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert resp2.status_code == 401


async def test_get_me_success(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"username": "eve", "password": "password123"},
    )
    token = reg.json()["access_token"]

    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["username"] == "eve"
    assert body["is_active"] is True


async def test_get_me_no_auth_header_returns_401(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401
    assert resp.json()["error"] == "authentication_error"


async def test_get_me_invalid_token_returns_401(client):
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not-a-jwt"},
    )
    assert resp.status_code == 401
    assert resp.json()["error"] == "authentication_error"
