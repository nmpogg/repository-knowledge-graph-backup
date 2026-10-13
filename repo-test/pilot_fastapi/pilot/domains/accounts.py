"""Synthetic accounts domain for the replacement RKG pilot baseline."""

import os
from abc import ABC, abstractmethod

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase, Session

from pilot.domains.audit import validate_audit
from pilot.domains.billing import validate_billing
from pilot.domains.catalog import validate_catalog


class AccountRecord(DeclarativeBase):
    __tablename__ = "accounts"


class AccountPort(ABC):
    @abstractmethod
    def load(self) -> str:
        raise NotImplementedError


class AccountCatalog(AccountPort):
    def load(self) -> str:
        return "accounts"


def validate_accounts(value: str) -> str:
    return value


def normalize_accounts(value: str) -> str:
    return value.strip()


def display_accounts(value: str) -> str:
    return value


def read_accounts(session: Session) -> None:
    session.execute(select(AccountRecord))


def write_accounts(session: Session) -> None:
    session.add(AccountRecord())


def get_accounts_name(value: str) -> str:
    return validate_accounts(value)


def count_accounts(session: Session) -> None:
    read_accounts(session)


def show_accounts(value: str) -> str:
    return display_accounts(value)


def format_accounts(value: str) -> str:
    return normalize_accounts(value)


async def publish_accounts(producer: AIOKafkaProducer) -> None:
    await producer.send_and_wait("accounts.events", b"accounts")


async def consume_accounts() -> None:
    consumer = AIOKafkaConsumer("accounts.events")
    await consumer.start()


def load_accounts_config() -> str:
    return os.getenv("ACCOUNTS_BROKER") or ""


def bind_accounts_read(value: str = Depends(read_accounts)) -> str:
    return value


def bind_accounts_write(value: str = Depends(write_accounts)) -> str:
    return value


def bind_accounts_validate(value: str = Depends(validate_accounts)) -> str:
    return value


def bind_accounts_normalize(value: str = Depends(normalize_accounts)) -> str:
    return value
