from app.core.exceptions import missing
from app.models.product import Category, ProductVariant
from app.repositories.base import Repository
from app.repositories.product_repo import ProductRepository
from app.schemas.product import ProductOut


class ProductService:
    def __init__(self, session):
        self.session = session
        self.products = ProductRepository(session)

    @staticmethod
    def public(product):
        result = ProductOut.model_validate(product)
        result.variants = [v for v in result.variants if v.is_active]
        return result

    async def require_category(self, category_id):
        category = await Repository(self.session, Category).get(category_id)
        if not category or not category.is_active:
            raise missing("Category")
        return category

    async def create(self, data):
        await self.require_category(data.category_id)
        product = await self.products.create(data.model_dump(exclude={"variants"}))
        for variant in data.variants:
            self.session.add(ProductVariant(product_id=product.id, **variant.model_dump()))
        await self.session.flush()
        return await self.products.detail(product.id, public=False)

    async def update(self, product_id, data):
        product = await self.products.get(product_id, lock=True)
        if not product:
            raise missing("Product")
        if data.category_id:
            await self.require_category(data.category_id)
        await self.products.update(product, data.model_dump(exclude_unset=True))
        return await self.products.detail(product_id, public=False)

    async def add_variant(self, product_id, data):
        if not await self.products.get(product_id, lock=True):
            raise missing("Product")
        return await Repository(self.session, ProductVariant).create(
            {"product_id": product_id, **data.model_dump()},
        )

    async def update_variant(self, product_id, variant_id, data):
        repository = Repository(self.session, ProductVariant)
        variant = await repository.get(variant_id, lock=True)
        if not variant or variant.product_id != product_id:
            raise missing("Variant")
        return await repository.update(variant, data.model_dump(exclude_unset=True))
