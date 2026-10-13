from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.models.product import Category, Product, ProductVariant
from app.repositories.base import Repository


class ProductRepository(Repository[Product]):
    def __init__(self, session):
        super().__init__(session, Product)

    async def detail(self, product_id: UUID, *, public: bool = True):
        query = (
            select(Product).options(selectinload(Product.variants)).where(Product.id == product_id)
        )
        if public:
            query = query.join(Category).where(Product.is_active, Category.is_active)
        return await self.session.scalar(query.execution_options(populate_existing=True))

    async def search(self, *, page, size, q=None, category_id=None, min_price=None, max_price=None):
        filters = [Product.is_active, Category.is_active]
        variant_filters = [ProductVariant.product_id == Product.id, ProductVariant.is_active]
        if q:
            # Escape wildcard characters: search is a literal substring.
            escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            filters.append(Product.name.ilike(f"%{escaped}%", escape="\\"))
        if category_id:
            filters.append(Product.category_id == category_id)
        if min_price is not None:
            variant_filters.append(ProductVariant.price >= min_price)
        if max_price is not None:
            variant_filters.append(ProductVariant.price <= max_price)
        filters.append(select(ProductVariant.id).where(*variant_filters).exists())
        query = select(Product).join(Category).where(*filters)
        total = await self.session.scalar(select(func.count()).select_from(query.subquery()))
        rows = await self.session.scalars(
            query.options(selectinload(Product.variants))
            .order_by(Product.created_at.desc(), Product.id)
            .offset((page - 1) * size)
            .limit(size),
        )
        return list(rows), total

    async def variants(self, ids, *, lock=False):
        if not ids:
            return {}
        query = select(ProductVariant).where(ProductVariant.id.in_(ids)).order_by(ProductVariant.id)
        if lock:
            query = query.with_for_update().execution_options(populate_existing=True)
        rows = await self.session.scalars(query)
        return {row.id: row for row in rows}

    async def product_context(self, variants):
        ids = {v.product_id for v in variants.values()}
        rows = (
            await self.session.execute(
                select(Product, Category).join(Category).where(Product.id.in_(ids)),
            )
        ).all()
        return {product.id: (product, category) for product, category in rows}
