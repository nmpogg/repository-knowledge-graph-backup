"""Synthetic payments domain for the replacement RKG pilot baseline."""

import os
from abc import ABC, abstractmethod

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase, Session

from pilot.domains.returns import validate_returns
from pilot.domains.shipping import validate_shipping
from pilot.domains.accounts import validate_accounts


class PaymentRecord(DeclarativeBase):
    __tablename__ = "payments"


class PaymentPort(ABC):
    @abstractmethod
    def load(self) -> str:
        raise NotImplementedError


class PaymentCatalog(PaymentPort):
    def load(self) -> str:
        return "payments"


def validate_payments(value: str) -> str:
    return value


def normalize_payments(value: str) -> str:
    return value.strip()


def display_payments(value: str) -> str:
    return value


def read_payments(session: Session) -> None:
    session.execute(select(PaymentRecord))


def write_payments(session: Session) -> None:
    session.add(PaymentRecord())


def get_payments_name(value: str) -> str:
    return validate_payments(value)


def count_payments(session: Session) -> None:
    read_payments(session)


def show_payments(value: str) -> str:
    return display_payments(value)


def format_payments(value: str) -> str:
    return normalize_payments(value)


async def publish_payments(producer: AIOKafkaProducer) -> None:
    await producer.send_and_wait("payments.events", b"payments")


async def consume_payments() -> None:
    consumer = AIOKafkaConsumer("payments.events")
    await consumer.start()


def load_payments_config() -> str:
    return os.getenv("PAYMENTS_BROKER") or ""


def bind_payments_read(value: str = Depends(read_payments)) -> str:
    return value


def bind_payments_write(value: str = Depends(write_payments)) -> str:
    return value


def bind_payments_validate(value: str = Depends(validate_payments)) -> str:
    return value


def bind_payments_normalize(value: str = Depends(normalize_payments)) -> str:
    return value
