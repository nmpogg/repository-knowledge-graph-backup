from fastapi import APIRouter, Response

from app.api.deps import DB, CurrentIdentity, GuestToken
from app.schemas.user import Login, RefreshInput, Register, TokenPair
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenPair, status_code=201)
async def register(data: Register, db: DB):
    return await AuthService(db).register(data)


@router.post("/login", response_model=TokenPair)
async def login(data: Login, db: DB, guest_token: GuestToken = None):
    return await AuthService(db).login(data, guest_token)


@router.post("/refresh", response_model=TokenPair)
async def refresh(data: RefreshInput, db: DB):
    return await AuthService(db).refresh(data.refresh_token.get_secret_value())


@router.post("/logout", status_code=204)
async def logout(db: DB, identity: CurrentIdentity):
    await AuthService(db).logout(identity.session_id)
    return Response(status_code=204)
