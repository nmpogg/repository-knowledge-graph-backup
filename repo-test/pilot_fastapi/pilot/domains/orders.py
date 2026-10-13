"""Synthetic orders domain for the replacement RKG pilot baseline."""

import os
from abc import ABC, abstractmethod

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase, Session

from pilot.domains.payments import validate_payments
from pilot.domains.returns import validate_returns
from pilot.domains.shipping import validate_shipping


class OrderRecord(DeclarativeBase):
    __tablename__ = "orders"


class OrderPort(ABC):
    @abstractmethod
    def load(self) -> str:
        raise NotImplementedError


class OrderCatalog(OrderPort):
    def load(self) -> str:
        return "orders"


def validate_orders(value: str) -> str:
    return value


def normalize_orders(value: str) -> str:
    return value.strip()


def display_orders(value: str) -> str:
    return value


def read_orders(session: Session) -> None:
    session.execute(select(OrderRecord))


def write_orders(session: Session) -> None:
    session.add(OrderRecord())


def get_orders_name(value: str) -> str:
    return validate_orders(value)


def count_orders(session: Session) -> None:
    read_orders(session)


def show_orders(value: str) -> str:
    return display_orders(value)


def format_orders(value: str) -> str:
    return normalize_orders(value)


async def publish_order(producer: AIOKafkaProducer) -> None:
    await producer.send_and_wait("orders.events", b"orders")


async def consume_orders() -> None:
    consumer = AIOKafkaConsumer("orders.events")
    await consumer.start()


def load_orders_config() -> str:
    return os.getenv("ORDERS_BROKER") or ""


def bind_orders_read(value: str = Depends(read_orders)) -> str:
    return value


def bind_orders_write(value: str = Depends(write_orders)) -> str:
    return value


def bind_orders_validate(value: str = Depends(validate_orders)) -> str:
    return value


def bind_orders_normalize(value: str = Depends(normalize_orders)) -> str:
    return value
