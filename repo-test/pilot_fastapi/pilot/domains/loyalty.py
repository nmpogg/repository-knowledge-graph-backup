"""Synthetic loyalty domain for the replacement RKG pilot baseline."""

import os
from abc import ABC, abstractmethod

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase, Session

from pilot.domains.notifications import validate_notifications
from pilot.domains.orders import validate_orders
from pilot.domains.payments import validate_payments


class LoyaltyRecord(DeclarativeBase):
    __tablename__ = "loyalty"


class LoyaltyPort(ABC):
    @abstractmethod
    def load(self) -> str:
        raise NotImplementedError


class LoyaltyCatalog(LoyaltyPort):
    def load(self) -> str:
        return "loyalty"


def validate_loyalty(value: str) -> str:
    return value


def normalize_loyalty(value: str) -> str:
    return value.strip()


def display_loyalty(value: str) -> str:
    return value


def read_loyalty(session: Session) -> None:
    session.execute(select(LoyaltyRecord))


def write_loyalty(session: Session) -> None:
    session.add(LoyaltyRecord())


def get_loyalty_name(value: str) -> str:
    return validate_loyalty(value)


def count_loyalty(session: Session) -> None:
    read_loyalty(session)


def show_loyalty(value: str) -> str:
    return display_loyalty(value)


def format_loyalty(value: str) -> str:
    return normalize_loyalty(value)


async def publish_loyalty(producer: AIOKafkaProducer) -> None:
    await producer.send_and_wait("loyalty.events", b"loyalty")


async def consume_loyalty() -> None:
    consumer = AIOKafkaConsumer("loyalty.events")
    await consumer.start()


def load_loyalty_config() -> str:
    return os.getenv("LOYALTY_BROKER") or ""


def bind_loyalty_read(value: str = Depends(read_loyalty)) -> str:
    return value


def bind_loyalty_write(value: str = Depends(write_loyalty)) -> str:
    return value


def bind_loyalty_validate(value: str = Depends(validate_loyalty)) -> str:
    return value


def bind_loyalty_normalize(value: str = Depends(normalize_loyalty)) -> str:
    return value
