"""Synthetic catalog domain for the replacement RKG pilot baseline."""

import os
from abc import ABC, abstractmethod

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase, Session

from pilot.domains.delivery import validate_delivery
from pilot.domains.inventory import validate_inventory
from pilot.domains.loyalty import validate_loyalty


class CatalogRecord(DeclarativeBase):
    __tablename__ = "catalog"


class CatalogPort(ABC):
    @abstractmethod
    def load(self) -> str:
        raise NotImplementedError


class CatalogCatalog(CatalogPort):
    def load(self) -> str:
        return "catalog"


def validate_catalog(value: str) -> str:
    return value


def normalize_catalog(value: str) -> str:
    return value.strip()


def display_catalog(value: str) -> str:
    return value


def read_catalog(session: Session) -> None:
    session.execute(select(CatalogRecord))


def write_catalog(session: Session) -> None:
    session.add(CatalogRecord())


def get_catalog_name(value: str) -> str:
    return validate_catalog(value)


def count_catalog(session: Session) -> None:
    read_catalog(session)


def show_catalog(value: str) -> str:
    return display_catalog(value)


def format_catalog(value: str) -> str:
    return normalize_catalog(value)


async def publish_catalog(producer: AIOKafkaProducer) -> None:
    await producer.send_and_wait("catalog.events", b"catalog")


async def consume_catalog() -> None:
    consumer = AIOKafkaConsumer("catalog.events")
    await consumer.start()


def load_catalog_config() -> str:
    return os.getenv("CATALOG_BROKER") or ""


def bind_catalog_read(value: str = Depends(read_catalog)) -> str:
    return value


def bind_catalog_write(value: str = Depends(write_catalog)) -> str:
    return value


def bind_catalog_validate(value: str = Depends(validate_catalog)) -> str:
    return value


def bind_catalog_normalize(value: str = Depends(normalize_catalog)) -> str:
    return value
