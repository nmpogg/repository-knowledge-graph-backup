"""Run periodically: python -m app.expire_orders. Each batch has its own transaction."""

import asyncio

from sqlalchemy import select

from app.core.database import get_engine, get_session_factory
from app.core.security import now
from app.models.order import Order, OrderStatus
from app.repositories.order_repo import OrderRepository
from app.repositories.product_repo import ProductRepository
from app.services.order_service import OrderService


async def expire_pending(batch_size=100):
    count = 0
    while True:
        async with get_session_factory()() as session, session.begin():
            ids = list(
                await session.scalars(
                    select(Order.id)
                    .where(
                        Order.status == OrderStatus.pending,
                        Order.expires_at <= now(),
                    )
                    .order_by(Order.id)
                    .limit(batch_size)
                    .with_for_update(skip_locked=True),
                )
            )
            if not ids:
                break
            # Lock the entire batch's variants in one sorted set to avoid inversion.
            orders = [await OrderRepository(session).detail(oid, lock=True) for oid in ids]
            variant_ids = {item.variant_id for order in orders for item in order.items}
            await ProductRepository(session).variants(variant_ids, lock=True)
            for order in orders:
                count += int(await OrderService(session).expire(order))
    return count


async def main():
    try:
        count = await expire_pending()
        print(f"Expired orders: {count}")
    finally:
        await get_engine().dispose()


if __name__ == "__main__":
    asyncio.run(main())
