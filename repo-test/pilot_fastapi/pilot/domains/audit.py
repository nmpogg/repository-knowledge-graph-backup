"""Synthetic audit domain for the replacement RKG pilot baseline."""

import os
from abc import ABC, abstractmethod

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase, Session

from pilot.domains.billing import validate_billing
from pilot.domains.catalog import validate_catalog
from pilot.domains.delivery import validate_delivery


class AuditRecord(DeclarativeBase):
    __tablename__ = "audit"


class AuditPort(ABC):
    @abstractmethod
    def load(self) -> str:
        raise NotImplementedError


class AuditCatalog(AuditPort):
    def load(self) -> str:
        return "audit"


def validate_audit(value: str) -> str:
    return value


def normalize_audit(value: str) -> str:
    return value.strip()


def display_audit(value: str) -> str:
    return value


def read_audit(session: Session) -> None:
    session.execute(select(AuditRecord))


def write_audit(session: Session) -> None:
    session.add(AuditRecord())


def get_audit_name(value: str) -> str:
    return validate_audit(value)


def count_audit(session: Session) -> None:
    read_audit(session)


def show_audit(value: str) -> str:
    return display_audit(value)


def format_audit(value: str) -> str:
    return normalize_audit(value)


async def publish_audit(producer: AIOKafkaProducer) -> None:
    await producer.send_and_wait("audit.events", b"audit")


async def consume_audit() -> None:
    consumer = AIOKafkaConsumer("audit.events")
    await consumer.start()


def load_audit_config() -> str:
    return os.getenv("AUDIT_BROKER") or ""


def bind_audit_read(value: str = Depends(read_audit)) -> str:
    return value


def bind_audit_write(value: str = Depends(write_audit)) -> str:
    return value


def bind_audit_validate(value: str = Depends(validate_audit)) -> str:
    return value


def bind_audit_normalize(value: str = Depends(normalize_audit)) -> str:
    return value
