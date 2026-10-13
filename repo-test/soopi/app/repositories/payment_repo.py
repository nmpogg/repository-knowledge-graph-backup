from sqlalchemy import select

from app.models.order import PaymentAttempt
from app.repositories.base import Repository


class PaymentRepository(Repository[PaymentAttempt]):
    def __init__(self, session):
        super().__init__(session, PaymentAttempt)

    async def by_order(self, order_id):
        return await self.session.scalar(
            select(PaymentAttempt).where(PaymentAttempt.order_id == order_id),
        )

    async def reload(self, attempt):
        await self.session.refresh(attempt)
        return attempt
