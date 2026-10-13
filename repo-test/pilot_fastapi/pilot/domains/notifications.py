"""Synthetic notifications domain for the replacement RKG pilot baseline."""

import os
from abc import ABC, abstractmethod

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase, Session

from pilot.domains.orders import validate_orders
from pilot.domains.payments import validate_payments
from pilot.domains.returns import validate_returns


class NotificationRecord(DeclarativeBase):
    __tablename__ = "notifications"


class NotificationPort(ABC):
    @abstractmethod
    def load(self) -> str:
        raise NotImplementedError


class NotificationCatalog(NotificationPort):
    def load(self) -> str:
        return "notifications"


def validate_notifications(value: str) -> str:
    return value


def normalize_notifications(value: str) -> str:
    return value.strip()


def display_notifications(value: str) -> str:
    return value


def read_notifications(session: Session) -> None:
    session.execute(select(NotificationRecord))


def write_notifications(session: Session) -> None:
    session.add(NotificationRecord())


def get_notifications_name(value: str) -> str:
    return validate_notifications(value)


def count_notifications(session: Session) -> None:
    read_notifications(session)


def show_notifications(value: str) -> str:
    return display_notifications(value)


def format_notifications(value: str) -> str:
    return normalize_notifications(value)


async def publish_notifications(producer: AIOKafkaProducer) -> None:
    await producer.send_and_wait("notifications.events", b"notifications")


async def consume_notifications() -> None:
    consumer = AIOKafkaConsumer("notifications.events")
    await consumer.start()


def load_notifications_config() -> str:
    return os.getenv("NOTIFICATIONS_BROKER") or ""


def bind_notifications_read(value: str = Depends(read_notifications)) -> str:
    return value


def bind_notifications_write(value: str = Depends(write_notifications)) -> str:
    return value


def bind_notifications_validate(value: str = Depends(validate_notifications)) -> str:
    return value


def bind_notifications_normalize(value: str = Depends(normalize_notifications)) -> str:
    return value
