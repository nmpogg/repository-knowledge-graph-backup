from fastapi import APIRouter

from app.api.v1.endpoints import auth, cart, categories, orders, products, users

router = APIRouter(prefix="/api/v1")
for module in (auth, users, products, categories, cart, orders):
    router.include_router(module.router)
