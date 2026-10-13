"""Built-in adapters loaded by the index coordinator.

Adding a language is a registration here. The coordinator does not name
individual language or framework classes.
"""

from __future__ import annotations

from rkg.adapters.aiokafka_messaging import AIOKafkaMessagingAdapter
from rkg.adapters.bullmq_messaging import BullMQMessagingAdapter
from rkg.adapters.django_framework import DjangoFrameworkAdapter
from rkg.adapters.express_framework import ExpressFrameworkAdapter
from rkg.adapters.fastapi_framework import FastAPIFrameworkAdapter
from rkg.adapters.flask_framework import FlaskFrameworkAdapter
from rkg.adapters.go_http_framework import GoHTTPFrameworkAdapter
from rkg.adapters.go_language import GoLanguageAdapter
from rkg.adapters.java_language import JavaLanguageAdapter
from rkg.adapters.jpa_data import JpaDataAccessAdapter
from rkg.adapters.kafka_go_messaging import KafkaGoMessagingAdapter
from rkg.adapters.nest_framework import NestFrameworkAdapter
from rkg.adapters.next_framework import NextFrameworkAdapter
from rkg.adapters.nuxt_framework import NuxtFrameworkAdapter
from rkg.adapters.pgx_data import PgxDataAccessAdapter
from rkg.adapters.python_language import PythonLanguageAdapter
from rkg.adapters.react_router_framework import ReactRouterFrameworkAdapter
from rkg.adapters.spring_framework import SpringFrameworkAdapter
from rkg.adapters.spring_kafka_messaging import SpringKafkaMessagingAdapter
from rkg.adapters.sqlalchemy_data import SQLAlchemyDataAccessAdapter
from rkg.adapters.tanstack_router_framework import TanStackRouterFrameworkAdapter
from rkg.adapters.typescript_language import TypeScriptLanguageAdapter
from rkg.adapters.vue_language import VueLanguageAdapter
from rkg.adapters.vue_router_framework import VueRouterFrameworkAdapter


def builtin_adapters() -> tuple[object, ...]:
    return (
        PythonLanguageAdapter(),
        FastAPIFrameworkAdapter(),
        FlaskFrameworkAdapter(),
        DjangoFrameworkAdapter(),  # orchestrator-pkg-7
        SQLAlchemyDataAccessAdapter(),
        AIOKafkaMessagingAdapter(),
        TypeScriptLanguageAdapter(),
        ReactRouterFrameworkAdapter(),
        TanStackRouterFrameworkAdapter(),  # orchestrator-pkg-4
        BullMQMessagingAdapter(),
        VueLanguageAdapter(),
        NuxtFrameworkAdapter(),
        NextFrameworkAdapter(),  # orchestrator-pkg-3
        JavaLanguageAdapter(),
        SpringFrameworkAdapter(),
        JpaDataAccessAdapter(),
        SpringKafkaMessagingAdapter(),
        GoLanguageAdapter(),
        KafkaGoMessagingAdapter(),
        PgxDataAccessAdapter(),
        ExpressFrameworkAdapter(),  # orchestrator-pkg-5
        NestFrameworkAdapter(),  # orchestrator-pkg-5
        GoHTTPFrameworkAdapter(),  # orchestrator-pkg-9
        VueRouterFrameworkAdapter(),  # orchestrator-pkg-2
    )
