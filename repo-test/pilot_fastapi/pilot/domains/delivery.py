"""Synthetic delivery domain for the replacement RKG pilot baseline."""

import os
from abc import ABC, abstractmethod

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase, Session

from pilot.domains.inventory import validate_inventory
from pilot.domains.loyalty import validate_loyalty
from pilot.domains.notifications import validate_notifications


class DeliveryRecord(DeclarativeBase):
    __tablename__ = "delivery"


class DeliveryPort(ABC):
    @abstractmethod
    def load(self) -> str:
        raise NotImplementedError


class DeliveryCatalog(DeliveryPort):
    def load(self) -> str:
        return "delivery"


def validate_delivery(value: str) -> str:
    return value


def normalize_delivery(value: str) -> str:
    return value.strip()


def display_delivery(value: str) -> str:
    return value


def read_delivery(session: Session) -> None:
    session.execute(select(DeliveryRecord))


def write_delivery(session: Session) -> None:
    session.add(DeliveryRecord())


def get_delivery_name(value: str) -> str:
    return validate_delivery(value)


def count_delivery(session: Session) -> None:
    read_delivery(session)


def show_delivery(value: str) -> str:
    return display_delivery(value)


def format_delivery(value: str) -> str:
    return normalize_delivery(value)


async def publish_delivery(producer: AIOKafkaProducer) -> None:
    await producer.send_and_wait("delivery.events", b"delivery")


async def consume_delivery() -> None:
    consumer = AIOKafkaConsumer("delivery.events")
    await consumer.start()


def load_delivery_config() -> str:
    return os.getenv("DELIVERY_BROKER") or ""


def bind_delivery_read(value: str = Depends(read_delivery)) -> str:
    return value


def bind_delivery_write(value: str = Depends(write_delivery)) -> str:
    return value


def bind_delivery_validate(value: str = Depends(validate_delivery)) -> str:
    return value


def bind_delivery_normalize(value: str = Depends(normalize_delivery)) -> str:
    return value
