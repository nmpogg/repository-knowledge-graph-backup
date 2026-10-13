"""Offline schema, reference, route and native constant consistency checks."""

import json
import re
from pathlib import Path

from jsonschema import Draft7Validator, FormatChecker
from jsonschema.validators import validator_for

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text())


def source(path):
    return (ROOT / path).read_text()


def resolve(doc, pointer):
    if not pointer.startswith("#/"):
        raise ValueError("external_contract_reference")
    value = doc
    for part in pointer[2:].split("/"):
        value = value[part.replace("~1", "/").replace("~0", "~")]
    return value


def refs(value, document):
    if isinstance(value, dict):
        if isinstance(value.get("$ref"), str):
            resolve(document, value["$ref"])
        for child in value.values():
            refs(child, document)
    elif isinstance(value, list):
        for child in value:
            refs(child, document)


def validate_schema(schema, document):
    cls = validator_for(schema)
    cls.check_schema(schema)
    cls(schema, format_checker=FormatChecker()).validate(document)


def check_routes(api):
    text = source(
        "services/orders/src/main/java/com/example/rkgfixture/orders/api/OrderController.java"
    )
    base = re.search(r'BASE_PATH\s*=\s*"([^"]+)"', text).group(1)
    constants = dict(re.findall(r'(\w+)\s*=\s*"([^"]+)"', text))
    actual = set()
    for match in re.finditer(r"@(Get|Post|Patch)Mapping(?:\(([^\n]*)\))?", text):
        method, args = match.groups()
        args = args or ""
        path = ""
        literal = re.search(r'"([^"]*)"', args)
        if literal:
            path = literal.group(1)
        named = re.search(r"path\s*=\s*(\w+)", args)
        if named:
            path = constants[named.group(1)]
        actual.add((method.upper(), base + path))
    for match in re.finditer(
        r'@RequestMapping\(path\s*=\s*"([^"]+)",\s*method\s*=\s*\{([^}]+)\}', text
    ):
        for method in re.findall(r"RequestMethod\.(\w+)", match.group(2)):
            actual.add((method, base + match.group(1)))
    expected = {
        (method.upper(), path)
        for path, methods in api["paths"].items()
        for method in methods
    }
    assert actual == expected, "route_contract_mismatch"
    operations = [
        op["operationId"]
        for methods in api["paths"].values()
        for op in methods.values()
    ]
    assert len(operations) == len(set(operations)), "duplicate_operation_id"
    for path, methods in api["paths"].items():
        parameters = set(re.findall(r"\{([^}]+)\}", path))
        for op in methods.values():
            declared = {
                p["name"]
                for p in op.get("parameters", [])
                if p.get("in") == "path" and p.get("required")
            }
            assert parameters == declared, "path_parameter_mismatch"
    client = source("apps/web/src/services/orderApi.ts")
    for method in ("get", "post"):
        assert f"this.client.{method}<" in client and "'/api/orders'" in client
    assert "this.client.patch<Order>" in client and "/status`" in client
    enum = source(
        "services/orders/src/main/java/com/example/rkgfixture/orders/domain/OrderStatus.java"
    )
    ts = source("apps/web/src/domain/order.ts")
    for status in api["components"]["schemas"]["Order"]["properties"]["status"]["enum"]:
        assert status in enum and "'" + status + "'" in ts, "status_contract_mismatch"


def verify():
    api = load("contracts/openapi/orders-api.yaml")
    events = load("contracts/asyncapi/order-events.yaml")
    validate_schema(load("contracts/schemas/openapi-3.0.json"), api)
    validate_schema(load("contracts/schemas/asyncapi-2.6.json"), events)
    refs(api, api)
    refs(events, events)
    check_routes(api)
    assert set(events["channels"]) == {
        "orders.events",
        "orders.projection.updated",
        "order-email",
    }
    operations = [
        op["operationId"]
        for channel in events["channels"].values()
        for key, op in channel.items()
        if key in {"publish", "subscribe"}
    ]
    assert len(operations) == len(set(operations)), "duplicate_async_operation_id"
    assert not events.get("servers"), "fixture_contract_requires_no_broker"
    for topic, paths in {
        "orders.events": [
            "services/orders/src/main/java/com/example/rkgfixture/orders/messaging/MessagingTopics.java",
            "workers/projection/internal/messaging/kafka_consumer.go",
            "workers/email/src/domain/events.ts",
        ],
        "orders.projection.updated": [
            "workers/projection/internal/messaging/topics.go"
        ],
        "order-email": [
            "workers/email/src/queues/emailQueue.ts",
            "workers/email/src/queues/names.ts",
        ],
    }.items():
        for path in paths:
            assert topic in source(path), "channel_contract_mismatch"
    for message, example in [
        ("OrderEvent", "order-event"),
        ("ProjectionUpdated", "projection-updated"),
    ]:
        Draft7Validator(
            events["components"]["messages"][message]["payload"],
            format_checker=FormatChecker(),
        ).validate(load("contracts/examples/" + example + ".json"))
    # Native tests also prove Java serialization and Go/TS event acceptance.
    for name in ["OrderRequest", "Order"]:
        sample = load(
            "contracts/examples/"
            + ("order-request" if name == "OrderRequest" else "order-response")
            + ".json"
        )
        schema = api["components"]["schemas"][name]
        # Resolve local item references without permitting network retrieval.
        schema = json.loads(json.dumps(schema))
        if "items" in schema.get("properties", {}):
            schema["properties"]["items"]["items"] = api["components"]["schemas"][
                "OrderItem"
            ]
        Draft7Validator(schema).validate(sample)


if __name__ == "__main__":
    verify()
    print("Contract schemas, local references, routes, channels and examples passed.")
