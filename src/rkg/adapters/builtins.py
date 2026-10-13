"""Built-in adapters loaded by the index coordinator.

Adding a language is a registration here. The coordinator does not name
individual language or framework classes.
"""

from __future__ import annotations

from rkg.adapters.aiokafka_messaging import AIOKafkaMessagingAdapter
from rkg.adapters.bullmq_messaging import BullMQMessagingAdapter
from rkg.adapters.fastapi_framework import FastAPIFrameworkAdapter
from rkg.adapters.flask_framework import FlaskFrameworkAdapter
from rkg.adapters.go_language import GoLanguageAdapter
from rkg.adapters.java_language import JavaLanguageAdapter
from rkg.adapters.jpa_data import JpaDataAccessAdapter
from rkg.adapters.kafka_go_messaging import KafkaGoMessagingAdapter
from rkg.adapters.nuxt_framework import NuxtFrameworkAdapter
from rkg.adapters.pgx_data import PgxDataAccessAdapter
from rkg.adapters.python_language import PythonLanguageAdapter
from rkg.adapters.react_router_framework import ReactRouterFrameworkAdapter
from rkg.adapters.spring_framework import SpringFrameworkAdapter
from rkg.adapters.spring_kafka_messaging import SpringKafkaMessagingAdapter
from rkg.adapters.sqlalchemy_data import SQLAlchemyDataAccessAdapter
from rkg.adapters.typescript_language import TypeScriptLanguageAdapter
from rkg.adapters.vue_language import VueLanguageAdapter


def builtin_adapters() -> tuple[object, ...]:
    return (
        PythonLanguageAdapter(),
        FastAPIFrameworkAdapter(),
        FlaskFrameworkAdapter(),
        SQLAlchemyDataAccessAdapter(),
        AIOKafkaMessagingAdapter(),
        TypeScriptLanguageAdapter(),
        ReactRouterFrameworkAdapter(),
        BullMQMessagingAdapter(),
        VueLanguageAdapter(),
        NuxtFrameworkAdapter(),
        JavaLanguageAdapter(),
        SpringFrameworkAdapter(),
        JpaDataAccessAdapter(),
        SpringKafkaMessagingAdapter(),
        GoLanguageAdapter(),
        KafkaGoMessagingAdapter(),
        PgxDataAccessAdapter(),
    )
