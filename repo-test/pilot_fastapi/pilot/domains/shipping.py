"""Synthetic shipping domain for the replacement RKG pilot baseline."""

import os
from abc import ABC, abstractmethod

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase, Session

from pilot.domains.accounts import validate_accounts
from pilot.domains.audit import validate_audit
from pilot.domains.billing import validate_billing


class ShipmentRecord(DeclarativeBase):
    __tablename__ = "shipping"


class ShipmentPort(ABC):
    @abstractmethod
    def load(self) -> str:
        raise NotImplementedError


class ShipmentCatalog(ShipmentPort):
    def load(self) -> str:
        return "shipping"


def validate_shipping(value: str) -> str:
    return value


def normalize_shipping(value: str) -> str:
    return value.strip()


def display_shipping(value: str) -> str:
    return value


def read_shipping(session: Session) -> None:
    session.execute(select(ShipmentRecord))


def write_shipping(session: Session) -> None:
    session.add(ShipmentRecord())


def get_shipping_name(value: str) -> str:
    return validate_shipping(value)


def count_shipping(session: Session) -> None:
    read_shipping(session)


def show_shipping(value: str) -> str:
    return display_shipping(value)


def format_shipping(value: str) -> str:
    return normalize_shipping(value)


async def publish_shipping(producer: AIOKafkaProducer) -> None:
    await producer.send_and_wait("shipping.events", b"shipping")


async def consume_shipping() -> None:
    consumer = AIOKafkaConsumer("shipping.events")
    await consumer.start()


def load_shipping_config() -> str:
    return os.getenv("SHIPPING_BROKER") or ""


def bind_shipping_read(value: str = Depends(read_shipping)) -> str:
    return value


def bind_shipping_write(value: str = Depends(write_shipping)) -> str:
    return value


def bind_shipping_validate(value: str = Depends(validate_shipping)) -> str:
    return value


def bind_shipping_normalize(value: str = Depends(normalize_shipping)) -> str:
    return value
