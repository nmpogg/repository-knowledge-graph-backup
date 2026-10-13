from decimal import Decimal
from types import SimpleNamespace

import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models import Address, Base, Cart, CartItem, Category, Product, ProductVariant, User


@pytest.fixture(autouse=True)
def settings(monkeypatch):
    values = {
        "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
        "JWT_SECRET": "test-only-key-with-at-least-32-characters",
        "SHIPPING_FEE": "30000",
        "TRUSTED_HOSTS": '["testserver","localhost"]',
        "MOMO_PARTNER_CODE": "TEST",
        "MOMO_ACCESS_KEY": "test-access",
        "MOMO_SECRET_KEY": "test-momo-secret",
        "MOMO_REDIRECT_URL": "https://store.example/result",
        "MOMO_IPN_URL": "https://api.example/ipn",
        "VNPAY_TMN_CODE": "TEST",
        "VNPAY_HASH_SECRET": "test-vnpay-secret",
        "VNPAY_RETURN_URL": "https://store.example/result",
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    get_settings.cache_clear()
    yield get_settings()
    get_settings.cache_clear()


@pytest.fixture
async def factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    @event.listens_for(engine.sync_engine, "connect")
    def enable_foreign_keys(connection, record):
        connection.execute("PRAGMA foreign_keys=ON")

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    await engine.dispose()


@pytest.fixture
async def db(factory):
    async with factory() as session:
        yield session


@pytest.fixture
async def seed(db):
    user = User(email="buyer@example.com", password_hash="unused", full_name="Buyer")
    other = User(email="other@example.com", password_hash="unused", full_name="Other")
    category = Category(name="Clothes", slug="clothes")
    db.add_all([user, other, category])
    await db.flush()
    address = Address(
        user_id=user.id,
        recipient="Buyer",
        phone="0901234567",
        line1="12 Example street",
        ward="Ward",
        district="District",
        province="Province",
    )
    product = Product(category_id=category.id, name="T-Shirt", slug="t-shirt")
    db.add_all([address, product])
    await db.flush()
    variant = ProductVariant(
        product_id=product.id,
        sku="SHIRT-M",
        name="Medium",
        price=Decimal(100000),
        stock=10,
    )
    db.add(variant)
    await db.flush()
    cart = Cart(user_id=user.id, items=[CartItem(variant_id=variant.id, quantity=2)])
    db.add(cart)
    await db.commit()
    return SimpleNamespace(
        user=user,
        other=other,
        address=address,
        product=product,
        variant=variant,
        category=category,
        cart=cart,
    )
