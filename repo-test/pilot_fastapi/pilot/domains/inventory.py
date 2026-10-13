"""Synthetic inventory domain for the replacement RKG pilot baseline."""

import os
from abc import ABC, abstractmethod

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase, Session

from pilot.domains.loyalty import validate_loyalty
from pilot.domains.notifications import validate_notifications
from pilot.domains.orders import validate_orders


class InventoryRecord(DeclarativeBase):
    __tablename__ = "inventory"


class InventoryPort(ABC):
    @abstractmethod
    def load(self) -> str:
        raise NotImplementedError


class InventoryCatalog(InventoryPort):
    def load(self) -> str:
        return "inventory"


def validate_inventory(value: str) -> str:
    return value


def normalize_inventory(value: str) -> str:
    return value.strip()


def display_inventory(value: str) -> str:
    return value


def read_inventory(session: Session) -> None:
    session.execute(select(InventoryRecord))


def write_inventory(session: Session) -> None:
    session.add(InventoryRecord())


def get_inventory_name(value: str) -> str:
    return validate_inventory(value)


def count_inventory(session: Session) -> None:
    read_inventory(session)


def show_inventory(value: str) -> str:
    return display_inventory(value)


def format_inventory(value: str) -> str:
    return normalize_inventory(value)


async def publish_inventory(producer: AIOKafkaProducer) -> None:
    await producer.send_and_wait("inventory.events", b"inventory")


async def consume_inventory() -> None:
    consumer = AIOKafkaConsumer("inventory.events")
    await consumer.start()


def load_inventory_config() -> str:
    return os.getenv("INVENTORY_BROKER") or ""


def bind_inventory_read(value: str = Depends(read_inventory)) -> str:
    return value


def bind_inventory_write(value: str = Depends(write_inventory)) -> str:
    return value


def bind_inventory_validate(value: str = Depends(validate_inventory)) -> str:
    return value


def bind_inventory_normalize(value: str = Depends(normalize_inventory)) -> str:
    return value
