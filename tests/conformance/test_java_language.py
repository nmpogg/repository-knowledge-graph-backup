"""Focused conformance for the Java language adapter."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from rkg.adapters import AdapterContext
from rkg.domain import EdgeType, SourceScanConfig, validate_fact_batch
from rkg.ingestion import LocalSourcePolicy, build_manifest, resolve_local_source

_JAVA_PATTERNS = ("*.java", "**/*.java", "*.yml", "**/*.yml")
_SECRET = "RKG_TEST_SECRET_DO_NOT_PERSIST"


def _adapter():
    from rkg.adapters.java_language import JavaLanguageAdapter

    return JavaLanguageAdapter()


def _write(root: Path, relative: str, source: str) -> None:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")


def _run(root: Path):
    config = SourceScanConfig(40, 65536, _JAVA_PATTERNS)
    manifest = build_manifest(
        resolve_local_source("repo-java", root, LocalSourcePolicy((root,))), config
    )
    context = AdapterContext("repo-java", "snap-java", "job-java", config)
    adapter = _adapter()
    assert adapter.detect(manifest).technologies
    parsed = adapter.parse(manifest, config)
    extracted = adapter.extract(context, parsed)
    resolved = adapter.resolve(context, parsed, extracted.facts)
    validate_fact_batch(resolved.facts)
    return resolved


def _names(resolved) -> set[str]:
    return {item.qualified_name for item in resolved.facts.entities}


def _edges(resolved, edge_type: EdgeType) -> set[tuple[str, str]]:
    by_id = {item.id: item for item in resolved.facts.entities}
    return {
        (by_id[edge.source_id].qualified_name, by_id[edge.target_id].qualified_name)
        for edge in resolved.facts.edges
        if edge.type == edge_type and edge.source_id in by_id
    }


def test_types_callables_inherits_and_overloads(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "src/main/java/com/example/rkgfixture/orders/domain/Order.java",
        """
package com.example.rkgfixture.orders.domain;
import java.util.List;
public record Order(String id, List<OrderItem> items) {
  public static Order create(String id) { return create(id, List.of()); }
  public static Order create(String id, List<OrderItem> items) {
    return new Order(id, items);
  }
  public static final class Summary {}
}
""".strip(),
    )
    _write(
        tmp_path,
        "src/main/java/com/example/rkgfixture/orders/domain/OrderItem.java",
        """
package com.example.rkgfixture.orders.domain;
public record OrderItem(String sku) {}
""".strip(),
    )
    _write(
        tmp_path,
        "src/main/java/com/example/rkgfixture/orders/domain/OrderNotFoundException.java",
        """
package com.example.rkgfixture.orders.domain;
public class OrderNotFoundException extends RuntimeException {
  public OrderNotFoundException(String id) { super(id); }
}
""".strip(),
    )
    resolved = _run(tmp_path)
    names = _names(resolved)
    assert "domain.Order" in names
    assert "domain.Order.create(String)" in names
    assert "domain.Order.create(String, List<OrderItem>)" in names
    assert "domain.Order.Summary" in names
    assert (
        "domain.OrderNotFoundException",
        "RuntimeException",
    ) in _edges(resolved, EdgeType.INHERITS_FROM)


def test_constructor_depends_on_and_config_keys(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "src/main/java/com/example/rkgfixture/orders/application/OrderService.java",
        """
package com.example.rkgfixture.orders.application;
public interface OrderService {}
""".strip(),
    )
    _write(
        tmp_path,
        "src/main/java/com/example/rkgfixture/orders/api/OrderController.java",
        """
package com.example.rkgfixture.orders.api;
import com.example.rkgfixture.orders.application.OrderService;
public class OrderController {
  public OrderController(OrderService orderService) {}
}
""".strip(),
    )
    _write(
        tmp_path,
        "src/main/resources/application.yml",
        """
spring:
  datasource:
    url: ${ORDERS_DATASOURCE_URL:jdbc:h2:mem:x}
  kafka:
    listener:
      auto-startup: false
orders:
  enabled: ${ORDERS_ENABLED:true}
""".strip(),
    )
    resolved = _run(tmp_path)
    assert (
        "api.OrderController",
        "application.OrderService",
    ) in _edges(resolved, EdgeType.DEPENDS_ON)
    names = _names(resolved)
    assert "environment:ORDERS_DATASOURCE_URL" in names
    assert "environment:ORDERS_ENABLED" in names
    assert "spring.kafka.listener.auto-startup" in names
    blob = json.dumps(
        {
            "entities": [asdict(item) for item in resolved.facts.entities],
            "diagnostics": [asdict(item) for item in resolved.facts.diagnostics],
        }
    )
    assert _SECRET not in blob
    assert "jdbc:h2" not in blob


def test_ambiguous_marker_is_diagnostic_only(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "src/main/java/com/example/rkgfixture/orders/analysiscases/positive/Marker.java",
        """
package com.example.rkgfixture.orders.analysiscases.positive;
public class Marker {}
""".strip(),
    )
    _write(
        tmp_path,
        "src/main/java/com/example/rkgfixture/orders/analysiscases/negative/Marker.java",
        """
package com.example.rkgfixture.orders.analysiscases.negative;
public class Marker {}
""".strip(),
    )
    _write(
        tmp_path,
        "src/main/java/com/example/rkgfixture/orders/analysiscases/UsesMarker.java",
        """
package com.example.rkgfixture.orders.analysiscases;
public final class UsesMarker {
  public UsesMarker(Marker marker) {}
}
""".strip(),
    )
    resolved = _run(tmp_path)
    codes = {item.code for item in resolved.facts.diagnostics}
    assert "java_binding_ambiguous" in codes
    assert not any(
        src.endswith("UsesMarker") for src, _ in _edges(resolved, EdgeType.DEPENDS_ON)
    )
