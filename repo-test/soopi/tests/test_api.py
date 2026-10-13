import httpx
import pytest
from sqlalchemy import select

from app.api.deps import get_db
from app.models import User


@pytest.fixture
async def client(db):
    from app.main import create_app

    app = create_app()

    async def override_db():
        try:
            yield db
            await db.commit()
        except BaseException:
            await db.rollback()
            raise

    app.dependency_overrides[get_db] = override_db
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        yield client


async def sign_up(client, email="api@example.com"):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "strong-password-123",
            "full_name": "API User",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


async def test_auth_and_permission_boundaries(client, db):
    assert (await client.get("/api/v1/users/me")).status_code == 401
    tokens = await sign_up(client)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    me = await client.get("/api/v1/users/me", headers=headers)
    assert me.status_code == 200
    assert "password_hash" not in me.json()
    assert not me.json()["is_admin"]
    denied = await client.post(
        "/api/v1/categories", headers=headers, json={"name": "Category", "slug": "category"}
    )
    assert denied.status_code == 403
    assert (await client.post("/api/v1/auth/logout", headers=headers)).status_code == 204
    assert (await client.get("/api/v1/users/me", headers=headers)).status_code == 401
    refreshed = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert refreshed.status_code == 401


async def test_validation_cannot_assign_admin_or_leak_password(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "api@example.com",
            "password": "xY7!zQ",
            "full_name": "API",
            "is_admin": True,
        },
    )
    assert response.status_code == 422
    assert "xY7!zQ" not in response.text
    assert "input" not in response.text


async def test_admin_catalog_and_search(client, db):
    tokens = await sign_up(client)
    user = await db.scalar(select(User).where(User.email == "api@example.com"))
    user.is_admin = True
    await db.commit()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    category = await client.post(
        "/api/v1/categories", headers=headers, json={"name": "Clothes", "slug": "clothes"}
    )
    assert category.status_code == 201
    response = await client.post(
        "/api/v1/products",
        headers=headers,
        json={
            "category_id": category.json()["id"],
            "name": "Cotton shirt",
            "slug": "cotton-shirt",
            "variants": [{"sku": "COTTON-M", "name": "M", "price": 100000, "stock": 10}],
        },
    )
    assert response.status_code == 201, response.text
    product_id = response.json()["id"]
    search = await client.get("/api/v1/products?q=shirt&min_price=90000&max_price=110000")
    assert search.status_code == 200
    assert search.json()["total"] == 1
    assert (await client.get("/api/v1/products?q=absent")).json()["total"] == 0
    assert (await client.get("/api/v1/products?min_price=20&max_price=10")).status_code == 422
    variant_id = response.json()["variants"][0]["id"]
    await client.patch(
        f"/api/v1/products/{product_id}/variants/{variant_id}",
        headers=headers,
        json={"is_active": False},
    )
    assert (await client.get(f"/api/v1/products/{product_id}")).json()["variants"] == []
    assert (await client.get("/api/v1/products")).json()["total"] == 0


async def test_full_checkout_and_ownership(client, seed):
    guest = await client.post("/api/v1/cart/guest")
    guest_headers = {"X-Guest-Token": guest.json()["guest_token"]}
    response = await client.post(
        "/api/v1/cart/items",
        headers=guest_headers,
        json={"variant_id": str(seed.variant.id), "quantity": 2},
    )
    assert response.status_code == 200
    assert (await client.get("/api/v1/cart")).status_code == 401
    tokens = await sign_up(client)
    login = await client.post(
        "/api/v1/auth/login",
        headers=guest_headers,
        json={"email": "api@example.com", "password": "strong-password-123"},
    )
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert (await client.get("/api/v1/cart", headers=guest_headers)).status_code == 401
    address = await client.post(
        "/api/v1/users/me/addresses",
        headers=headers,
        json={
            "recipient": "API User",
            "phone": "0901234567",
            "line1": "12 Example street",
            "ward": "Ward",
            "district": "District",
            "province": "Province",
        },
    )
    assert address.status_code == 201, address.text
    checkout = {"address_id": address.json()["id"], "payment_method": "cod"}
    assert (await client.post("/api/v1/orders", headers=headers, json=checkout)).status_code == 422
    headers["Idempotency-Key"] = "api-checkout-001"
    response = await client.post("/api/v1/orders", headers=headers, json=checkout)
    assert response.status_code == 201, response.text
    order_id = response.json()["id"]
    assert response.json()["total"] == 230000
    repeated = await client.post("/api/v1/orders", headers=headers, json=checkout)
    assert repeated.json()["id"] == order_id
    assert (await client.get("/api/v1/cart", headers=headers)).json()["items"] == []
    stranger = await sign_up(client, "stranger@example.com")
    stranger_headers = {"Authorization": f"Bearer {stranger['access_token']}"}
    assert (
        await client.get(f"/api/v1/orders/{order_id}", headers=stranger_headers)
    ).status_code == 404
    assert (
        await client.delete(
            f"/api/v1/users/me/addresses/{address.json()['id']}", headers=stranger_headers
        )
    ).status_code == 404
    cancelled = await client.post(f"/api/v1/orders/{order_id}/cancel", headers=headers)
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert tokens["token_type"] == "bearer"


async def test_invalid_webhooks_do_not_acknowledge_payment(client):
    duplicate = await client.get("/api/v1/orders/webhooks/vnpay?vnp_Amount=100&vnp_Amount=200")
    assert duplicate.json()["RspCode"] == "97"
    invalid = await client.get("/api/v1/orders/webhooks/vnpay?vnp_TmnCode=TEST&vnp_SecureHash=bad")
    assert invalid.json()["RspCode"] == "97"
    assert (await client.post("/api/v1/orders/webhooks/momo", json={})).status_code == 422
