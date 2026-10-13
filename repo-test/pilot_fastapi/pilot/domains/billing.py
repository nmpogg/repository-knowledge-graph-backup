"""Synthetic billing domain for the replacement RKG pilot baseline."""

import os
from abc import ABC, abstractmethod

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase, Session

from pilot.domains.catalog import validate_catalog
from pilot.domains.delivery import validate_delivery
from pilot.domains.inventory import validate_inventory


class BillingRecord(DeclarativeBase):
    __tablename__ = "billing"


class BillingPort(ABC):
    @abstractmethod
    def load(self) -> str:
        raise NotImplementedError


class BillingCatalog(BillingPort):
    def load(self) -> str:
        return "billing"


def validate_billing(value: str) -> str:
    return value


def normalize_billing(value: str) -> str:
    return value.strip()


def display_billing(value: str) -> str:
    return value


def read_billing(session: Session) -> None:
    session.execute(select(BillingRecord))


def write_billing(session: Session) -> None:
    session.add(BillingRecord())


def get_billing_name(value: str) -> str:
    return validate_billing(value)


def count_billing(session: Session) -> None:
    read_billing(session)


def show_billing(value: str) -> str:
    return display_billing(value)


def format_billing(value: str) -> str:
    return normalize_billing(value)


async def publish_billing(producer: AIOKafkaProducer) -> None:
    await producer.send_and_wait("billing.events", b"billing")


async def consume_billing() -> None:
    consumer = AIOKafkaConsumer("billing.events")
    await consumer.start()


def load_billing_config() -> str:
    return os.getenv("BILLING_BROKER") or ""


def bind_billing_read(value: str = Depends(read_billing)) -> str:
    return value


def bind_billing_write(value: str = Depends(write_billing)) -> str:
    return value


def bind_billing_validate(value: str = Depends(validate_billing)) -> str:
    return value


def bind_billing_normalize(value: str = Depends(normalize_billing)) -> str:
    return value
