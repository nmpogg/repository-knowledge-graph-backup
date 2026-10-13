"""Focused conformance for Spring / JPA / Spring Kafka adapters."""

from __future__ import annotations

from pathlib import Path

from rkg.adapters import AdapterContext
from rkg.domain import EdgeType, EntityType, SourceScanConfig, validate_fact_batch
from rkg.ingestion import LocalSourcePolicy, build_manifest, resolve_local_source

_PATTERNS = ("*.java", "**/*.java")


def _write(root: Path, relative: str, source: str) -> None:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")


def _pipeline(root: Path):
    from rkg.adapters.java_language import JavaLanguageAdapter
    from rkg.adapters.jpa_data import JpaDataAccessAdapter
    from rkg.adapters.spring_framework import SpringFrameworkAdapter
    from rkg.adapters.spring_kafka_messaging import SpringKafkaMessagingAdapter

    config = SourceScanConfig(40, 65536, _PATTERNS)
    manifest = build_manifest(
        resolve_local_source("repo-spring", root, LocalSourcePolicy((root,))), config
    )
    context = AdapterContext("repo-spring", "snap-spring", "job-spring", config)
    language = JavaLanguageAdapter()
    parsed = language.parse(manifest, config)
    batch = language.resolve(
        context, parsed, language.extract(context, parsed).facts
    ).facts
    for adapter in (
        SpringFrameworkAdapter(),
        JpaDataAccessAdapter(),
        SpringKafkaMessagingAdapter(),
    ):
        batch = adapter.extract(context, parsed, batch).facts
        validate_fact_batch(batch)
    return batch


def _entities(batch, entity_type: EntityType):
    return [item for item in batch.entities if item.type == entity_type]


def _edge_pairs(batch, edge_type: EdgeType) -> set[tuple[str, str]]:
    by_id = {item.id: item for item in batch.entities}
    return {
        (by_id[edge.source_id].qualified_name, by_id[edge.target_id].qualified_name)
        for edge in batch.edges
        if edge.type == edge_type and edge.source_id in by_id
    }


def test_spring_endpoints_and_negatives(tmp_path: Path) -> None:
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
import org.springframework.web.bind.annotation.*;
@RestController
@RequestMapping(OrderController.BASE_PATH)
public class OrderController {
  public static final String BASE_PATH = "/api/orders";
  public OrderController(OrderService orderService) {}
  @GetMapping("/{orderId}")
  public String get(@PathVariable String orderId) { return orderId; }
  @RequestMapping(path = "/readiness", method = {RequestMethod.GET, RequestMethod.HEAD})
  public String readiness() { return "ready"; }
}
""".strip(),
    )
    _write(
        tmp_path,
        "src/main/java/com/example/rkgfixture/orders/analysiscases/negative/UnregisteredController.java",
        """
package com.example.rkgfixture.orders.analysiscases.negative;
import org.springframework.web.bind.annotation.GetMapping;
public class UnregisteredController {
  @GetMapping("/internal/unregistered")
  public String hidden() { return "hidden"; }
}
""".strip(),
    )
    _write(
        tmp_path,
        "src/main/java/com/example/rkgfixture/orders/analysiscases/negative/DynamicPathController.java",
        """
package com.example.rkgfixture.orders.analysiscases.negative;
import org.springframework.web.bind.annotation.*;
@RequestMapping("${fixture.dynamic-path}")
public class DynamicPathController {
  @GetMapping("/status")
  public String dynamicStatus() { return "dynamic"; }
}
""".strip(),
    )
    batch = _pipeline(tmp_path)
    endpoints = {
        (
            item.qualified_name,
            dict(item.attributes).get("method"),
            dict(item.attributes).get("path"),
        )
        for item in _entities(batch, EntityType.ENDPOINT)
    }
    assert (
        "api.OrderController.get",
        "GET",
        "/api/orders/{orderId}",
    ) in endpoints
    assert (
        "api.OrderController.readiness",
        "GET",
        "/api/orders/readiness",
    ) in endpoints
    assert (
        "api.OrderController.readiness.head",
        "HEAD",
        "/api/orders/readiness",
    ) in endpoints
    assert not any("UnregisteredController" in qn for qn, *_ in endpoints)
    assert not any("DynamicPathController" in qn for qn, *_ in endpoints)


def test_jpa_resources_and_kafka_channels(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "src/main/java/com/example/rkgfixture/orders/persistence/OrderEntity.java",
        """
package com.example.rkgfixture.orders.persistence;
import jakarta.persistence.*;
@Entity
@Table(name = "orders", schema = "commerce")
public class OrderEntity { @Id private String id; }
""".strip(),
    )
    _write(
        tmp_path,
        "src/main/java/com/example/rkgfixture/orders/persistence/OrderItemEntity.java",
        """
package com.example.rkgfixture.orders.persistence;
import jakarta.persistence.*;
@Entity
@Table(name = "order_items", schema = "commerce")
public class OrderItemEntity { @Id private Long id; }
""".strip(),
    )
    _write(
        tmp_path,
        "src/main/java/com/example/rkgfixture/analysiscases/negative/AuditOrderEntity.java",
        """
package com.example.rkgfixture.analysiscases.negative;
import jakarta.persistence.*;
@Entity
@Table(name = "orders", schema = "audit")
public class AuditOrderEntity { @Id private String id; }
""".strip(),
    )
    _write(
        tmp_path,
        "src/main/java/com/example/rkgfixture/orders/application/OrderRepository.java",
        """
package com.example.rkgfixture.orders.application;
public interface OrderRepository {}
""".strip(),
    )
    _write(
        tmp_path,
        "src/main/java/com/example/rkgfixture/orders/persistence/JpaOrderRepository.java",
        """
package com.example.rkgfixture.orders.persistence;
import com.example.rkgfixture.orders.application.OrderRepository;
import org.springframework.stereotype.Repository;
@Repository
public class JpaOrderRepository implements OrderRepository {
  public JpaOrderRepository(OrderJpaRepository repository) {}
  public void save() {}
  public void findById() {}
}
""".strip(),
    )
    _write(
        tmp_path,
        "src/main/java/com/example/rkgfixture/orders/persistence/OrderJpaRepository.java",
        """
package com.example.rkgfixture.orders.persistence;
public interface OrderJpaRepository {}
""".strip(),
    )
    _write(
        tmp_path,
        "src/main/java/com/example/rkgfixture/orders/messaging/MessagingTopics.java",
        """
package com.example.rkgfixture.orders.messaging;
public final class MessagingTopics {
  public static final String ORDERS_EVENTS = "orders.events";
  public static final String PAYMENTS_EVENTS = "payments.events";
  private MessagingTopics() {}
}
""".strip(),
    )
    _write(
        tmp_path,
        "src/main/java/com/example/rkgfixture/orders/messaging/OrderEventPublisher.java",
        """
package com.example.rkgfixture.orders.messaging;
public interface OrderEventPublisher {
  void publish();
}
""".strip(),
    )
    _write(
        tmp_path,
        "src/main/java/com/example/rkgfixture/orders/messaging/KafkaOrderEventPublisher.java",
        """
package com.example.rkgfixture.orders.messaging;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;
@Component
public class KafkaOrderEventPublisher implements OrderEventPublisher {
  private final KafkaTemplate<String, Object> kafkaTemplate;
  public KafkaOrderEventPublisher(KafkaTemplate<String, Object> kafkaTemplate) {
    this.kafkaTemplate = kafkaTemplate;
  }
  public void publish() {
    kafkaTemplate.send(MessagingTopics.ORDERS_EVENTS, "id", "body");
  }
}
""".strip(),
    )
    _write(
        tmp_path,
        "src/main/java/com/example/rkgfixture/orders/application/OrderService.java",
        """
package com.example.rkgfixture.orders.application;
public interface OrderService {
  void applyPayment(String id);
}
""".strip(),
    )
    _write(
        tmp_path,
        "src/main/java/com/example/rkgfixture/orders/messaging/PaymentEventListener.java",
        """
package com.example.rkgfixture.orders.messaging;
import com.example.rkgfixture.orders.application.OrderService;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;
@Component
public class PaymentEventListener {
  private final OrderService orderService;
  public PaymentEventListener(OrderService orderService) {
    this.orderService = orderService;
  }
  @KafkaListener(topics = MessagingTopics.PAYMENTS_EVENTS)
  public void onPayment(String event) { orderService.applyPayment(event); }
}
""".strip(),
    )
    _write(
        tmp_path,
        "src/main/java/com/example/rkgfixture/orders/analysiscases/negative/DynamicTopicListener.java",
        """
package com.example.rkgfixture.orders.analysiscases.negative;
import org.springframework.kafka.annotation.KafkaListener;
public class DynamicTopicListener {
  @KafkaListener(topics = "#{systemProperties['fixture.topic']}")
  public void onDynamicTopic(String ignored) {}
}
""".strip(),
    )
    batch = _pipeline(tmp_path)
    resources = {
        item.qualified_name for item in _entities(batch, EntityType.DATA_RESOURCE)
    }
    assert "relational:commerce.orders" in resources
    assert "relational:commerce.order_items" in resources
    assert "relational:audit.orders" in resources
    maps = _edge_pairs(batch, EdgeType.MAPS_TO)
    assert ("persistence.OrderEntity", "relational:commerce.orders") in maps
    assert ("persistence.OrderItemEntity", "relational:commerce.order_items") in maps
    reads = _edge_pairs(batch, EdgeType.READS)
    writes = _edge_pairs(batch, EdgeType.WRITES)
    assert ("persistence.JpaOrderRepository", "relational:commerce.orders") in reads
    assert ("persistence.JpaOrderRepository", "relational:commerce.orders") in writes
    assert (
        "persistence.JpaOrderRepository.findById",
        "relational:commerce.orders",
    ) in reads
    assert (
        "persistence.JpaOrderRepository.save",
        "relational:commerce.orders",
    ) in writes
    assert not any(tgt.endswith("audit.orders") for _, tgt in reads | writes)
    assert (
        "messaging.KafkaOrderEventPublisher.publish",
        "orders.events",
    ) in _edge_pairs(batch, EdgeType.PUBLISHES)
    assert (
        "messaging.PaymentEventListener.onPayment",
        "payments.events",
    ) in _edge_pairs(batch, EdgeType.CONSUMES)
    assert not any(
        "DynamicTopicListener" in src
        for src, _ in _edge_pairs(batch, EdgeType.CONSUMES)
    )


def test_unique_implementer_calls_reach_repository_methods(tmp_path: Path) -> None:
    """Interface-typed DI fields also call the sole concrete implementer method."""
    _write(
        tmp_path,
        "src/main/java/com/example/rkgfixture/orders/application/OrderService.java",
        """
package com.example.rkgfixture.orders.application;
public interface OrderService {
  String getOrder(String orderId);
}
""".strip(),
    )
    _write(
        tmp_path,
        "src/main/java/com/example/rkgfixture/orders/application/OrderRepository.java",
        """
package com.example.rkgfixture.orders.application;
public interface OrderRepository {
  String findById(String orderId);
}
""".strip(),
    )
    _write(
        tmp_path,
        "src/main/java/com/example/rkgfixture/orders/application/DefaultOrderService.java",
        """
package com.example.rkgfixture.orders.application;
import org.springframework.stereotype.Service;
@Service
public class DefaultOrderService implements OrderService {
  private final OrderRepository repository;
  public DefaultOrderService(OrderRepository repository) { this.repository = repository; }
  public String getOrder(String orderId) { return repository.findById(orderId); }
}
""".strip(),
    )
    _write(
        tmp_path,
        "src/main/java/com/example/rkgfixture/orders/persistence/JpaOrderRepository.java",
        """
package com.example.rkgfixture.orders.persistence;
import com.example.rkgfixture.orders.application.OrderRepository;
import org.springframework.stereotype.Repository;
@Repository
public class JpaOrderRepository implements OrderRepository {
  public String findById(String orderId) { return orderId; }
  public void save() {}
}
""".strip(),
    )
    _write(
        tmp_path,
        "src/main/java/com/example/rkgfixture/orders/persistence/OrderEntity.java",
        """
package com.example.rkgfixture.orders.persistence;
import jakarta.persistence.*;
@Entity
@Table(name = "orders", schema = "commerce")
public class OrderEntity { @Id private String id; }
""".strip(),
    )
    _write(
        tmp_path,
        "src/main/java/com/example/rkgfixture/orders/api/OrderController.java",
        """
package com.example.rkgfixture.orders.api;
import com.example.rkgfixture.orders.application.OrderService;
import org.springframework.web.bind.annotation.*;
@RestController
@RequestMapping("/api/orders")
public class OrderController {
  private final OrderService orderService;
  public OrderController(OrderService orderService) { this.orderService = orderService; }
  @GetMapping("/{orderId}")
  public String get(@PathVariable String orderId) { return orderService.getOrder(orderId); }
}
""".strip(),
    )
    batch = _pipeline(tmp_path)
    calls = _edge_pairs(batch, EdgeType.CALLS)
    assert (
        "api.OrderController.get",
        "application.OrderService.getOrder",
    ) in calls
    assert (
        "api.OrderController.get",
        "application.DefaultOrderService.getOrder",
    ) in calls
    assert (
        "application.DefaultOrderService.getOrder",
        "application.OrderRepository.findById",
    ) in calls
    assert (
        "application.DefaultOrderService.getOrder",
        "persistence.JpaOrderRepository.findById",
    ) in calls
    reads = _edge_pairs(batch, EdgeType.READS)
    assert (
        "persistence.JpaOrderRepository.findById",
        "relational:commerce.orders",
    ) in reads


def test_static_filter_and_interceptor_registration(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "src/main/java/com/example/rkgfixture/orders/api/OrderController.java",
        """
package com.example.rkgfixture.orders.api;
import org.springframework.web.bind.annotation.*;
@RestController
@RequestMapping("/api/orders")
public class OrderController {
  @GetMapping("/{orderId}")
  public String get(@PathVariable String orderId) { return orderId; }
  @RequestMapping(path = "/readiness", method = {RequestMethod.GET, RequestMethod.HEAD})
  public String readiness() { return "ready"; }
}
""".strip(),
    )
    _write(
        tmp_path,
        "src/main/java/com/example/rkgfixture/orders/config/RequestAuditFilter.java",
        """
package com.example.rkgfixture.orders.config;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.FilterChain;
@Component
@Order(RequestAuditFilter.ORDER)
public class RequestAuditFilter extends OncePerRequestFilter {
  public static final int ORDER = 1;
  protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain) {}
}
""".strip(),
    )
    _write(
        tmp_path,
        "src/main/java/com/example/rkgfixture/orders/config/OrderAuditInterceptor.java",
        """
package com.example.rkgfixture.orders.config;
import org.springframework.web.servlet.HandlerInterceptor;
public class OrderAuditInterceptor implements HandlerInterceptor {}
""".strip(),
    )
    _write(
        tmp_path,
        "src/main/java/com/example/rkgfixture/orders/config/WebMvcConfig.java",
        """
package com.example.rkgfixture.orders.config;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.boot.web.servlet.FilterRegistrationBean;
@Configuration
public class WebMvcConfig implements WebMvcConfigurer {
  public void addInterceptors(InterceptorRegistry registry) {
    registry.addInterceptor(new OrderAuditInterceptor()).addPathPatterns("/api/orders/{orderId}").order(2);
  }
  @Bean
  public FilterRegistrationBean<RequestAuditFilter> audit() {
    FilterRegistrationBean<RequestAuditFilter> bean = new FilterRegistrationBean<>();
    bean.setFilter(new RequestAuditFilter());
    bean.addUrlPatterns("/api/orders/readiness");
    bean.setOrder(9);
    return bean;
  }
}
""".strip(),
    )
    _write(
        tmp_path,
        "src/main/java/com/example/rkgfixture/orders/analysiscases/negative/UnregisteredRequestFilter.java",
        """
package com.example.rkgfixture.orders.analysiscases.negative;
import org.springframework.web.filter.OncePerRequestFilter;
public class UnregisteredRequestFilter extends OncePerRequestFilter {}
""".strip(),
    )
    _write(
        tmp_path,
        "src/main/java/com/example/rkgfixture/orders/analysiscases/negative/DynamicInterceptorConfig.java",
        """
package com.example.rkgfixture.orders.analysiscases.negative;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.HandlerInterceptor;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
@Configuration
public class DynamicInterceptorConfig implements WebMvcConfigurer {
  public void addInterceptors(InterceptorRegistry registry) {
    HandlerInterceptor selected = select();
    registry.addInterceptor(selected).addPathPatterns("/api/orders/{orderId}");
  }
  private HandlerInterceptor select() { return null; }
}
""".strip(),
    )
    batch = _pipeline(tmp_path)
    types = {
        item.qualified_name: dict(item.attributes)
        for item in _entities(batch, EntityType.TYPE)
    }
    assert types["config.OrderAuditInterceptor"]["order"] == 2
    assert "order" not in types["analysiscases.negative.UnregisteredRequestFilter"]
    assert "order" not in types["config.RequestAuditFilter"]
    codes = {item.code for item in batch.diagnostics}
    assert "spring_filter_unregistered" in codes
    assert "spring_filter_ambiguous" in codes
    assert "spring_filter_order_ambiguous" in codes
    assert "spring_filter_target_ambiguous" in codes
    by_id = {item.id: item for item in batch.entities}
    evidence = {item.id: item for item in batch.evidence}
    attached = []
    for edge in batch.edges:
        if edge.type != EdgeType.HANDLED_BY:
            continue
        source = by_id[edge.source_id]
        rules = [(evidence[ref].rule, evidence[ref].file_path) for ref in edge.evidence_ids]
        if source.qualified_name == "api.OrderController.get":
            attached.extend(rules)
        if "readiness" in source.qualified_name:
            assert not any(rule == "RKG.spring.registration.v1" for rule, _path in rules)
    assert any(
        rule == "RKG.spring.registration.v1" and path.endswith("WebMvcConfig.java")
        for rule, path in attached
    )
    assert not any("DynamicInterceptorConfig" in path for _rule, path in attached)
    assert not any(
        edge.type == EdgeType.DEPENDS_ON and by_id[edge.source_id].type == EntityType.ENDPOINT
        for edge in batch.edges
        if edge.source_id in by_id
    )

