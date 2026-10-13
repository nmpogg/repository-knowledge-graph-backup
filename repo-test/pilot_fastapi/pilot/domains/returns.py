"""Synthetic returns domain for the replacement RKG pilot baseline."""

import os
from abc import ABC, abstractmethod

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase, Session

from pilot.domains.shipping import validate_shipping
from pilot.domains.accounts import validate_accounts
from pilot.domains.audit import validate_audit


class ReturnRecord(DeclarativeBase):
    __tablename__ = "returns"


class ReturnPort(ABC):
    @abstractmethod
    def load(self) -> str:
        raise NotImplementedError


class ReturnCatalog(ReturnPort):
    def load(self) -> str:
        return "returns"


def validate_returns(value: str) -> str:
    return value


def normalize_returns(value: str) -> str:
    return value.strip()


def display_returns(value: str) -> str:
    return value


def read_returns(session: Session) -> None:
    session.execute(select(ReturnRecord))


def write_returns(session: Session) -> None:
    session.add(ReturnRecord())


def get_returns_name(value: str) -> str:
    return validate_returns(value)


def count_returns(session: Session) -> None:
    read_returns(session)


def show_returns(value: str) -> str:
    return display_returns(value)


def format_returns(value: str) -> str:
    return normalize_returns(value)


async def publish_returns(producer: AIOKafkaProducer) -> None:
    await producer.send_and_wait("returns.events", b"returns")


async def consume_returns() -> None:
    consumer = AIOKafkaConsumer("returns.events")
    await consumer.start()


def load_returns_config() -> str:
    return os.getenv("RETURNS_BROKER") or ""


def bind_returns_read(value: str = Depends(read_returns)) -> str:
    return value


def bind_returns_write(value: str = Depends(write_returns)) -> str:
    return value


def bind_returns_validate(value: str = Depends(validate_returns)) -> str:
    return value


def bind_returns_normalize(value: str = Depends(normalize_returns)) -> str:
    return value
