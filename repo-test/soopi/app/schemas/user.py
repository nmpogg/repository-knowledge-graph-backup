from typing import Annotated

from pydantic import EmailStr, Field, SecretStr, field_validator

from app.schemas.common import Input, Name, NonNullPatch, Output

Phone = Annotated[str, Field(pattern=r"^\+?[0-9]{8,15}$")]


class Register(Input):
    email: EmailStr
    password: SecretStr = Field(min_length=10, max_length=128)
    full_name: Name

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value):
        return str(value).lower()


class Login(Input):
    email: EmailStr
    password: SecretStr = Field(min_length=1, max_length=128)


class RefreshInput(Input):
    refresh_token: SecretStr = Field(min_length=40, max_length=200)


class TokenPair(Input):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserOut(Output):
    email: EmailStr
    full_name: str
    phone: str | None
    is_admin: bool


class UserPatch(NonNullPatch):
    full_name: Name | None = None
    phone: Phone | None = None


class AddressInput(Input):
    recipient: Name
    phone: Phone
    line1: str = Field(min_length=1, max_length=255)
    ward: Name
    district: Name
    province: Name


class AddressOut(Output, AddressInput):
    pass
