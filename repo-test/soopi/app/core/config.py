from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Soopi"
    database_url: str
    jwt_secret: SecretStr = Field(min_length=32)
    jwt_issuer: str = "soopi"
    jwt_audience: str = "soopi-api"
    access_token_minutes: int = Field(default=15, ge=1, le=60)
    refresh_token_days: int = Field(default=30, ge=1, le=90)
    guest_cart_days: int = Field(default=7, ge=1, le=30)
    order_hold_minutes: int = Field(default=30, ge=5, le=1440)
    shipping_fee: int = Field(default=30000, ge=0, le=10000000)
    cors_origins: list[str] = ["http://localhost:3000"]
    trusted_hosts: list[str] = ["localhost", "127.0.0.1"]
    momo_partner_code: str = ""
    momo_access_key: SecretStr = SecretStr("")
    momo_secret_key: SecretStr = SecretStr("")
    momo_create_url: str = "https://test-payment.momo.vn/v2/gateway/api/create"
    momo_redirect_url: str = ""
    momo_ipn_url: str = ""
    vnpay_tmn_code: str = ""
    vnpay_hash_secret: SecretStr = SecretStr("")
    vnpay_pay_url: str = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"
    vnpay_return_url: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
