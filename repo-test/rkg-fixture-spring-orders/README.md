# rkg-fixture-spring-orders

`rkg-fixture-spring-orders` is a standalone Spring backend for a small order domain and a golden fixture for Java, Spring Web MVC, Spring Data JPA, dependency-injection, and Spring Kafka analysis. It contains no RKG implementation and its test suite needs no Docker, PostgreSQL, Kafka broker, or external network after Maven dependencies are cached.

## Stack and reproducible build

- Java 21 LTS (tested with Eclipse Temurin `21.0.12.1`).
- Spring Boot `3.5.16`, Spring Framework `6.2.19`, Spring Kafka `3.3.16`.
- Hibernate ORM `6.6.53.Final` and H2 `2.3.232` for deterministic in-memory tests/default local startup.
- JUnit 5, AssertJ, Mockito, MockMvc, and Spring Boot test slices.
- Maven Wrapper `3.9.11`; the POM pins the parent/plugin versions and build output timestamp.

```bash
./mvnw test
./mvnw verify
```

For local development, `./mvnw spring-boot:run` starts the MVC application with the safe H2/Kafka placeholder defaults in `application.yml`. Kafka listeners have auto-start disabled by default, so local startup does not contact a broker. Enable and configure infrastructure explicitly only when desired.

## Architecture

```text
HTTP -> OrderController -> OrderService (interface)
                           -> DefaultOrderService
                              -> OrderRepository -> JpaOrderRepository -> OrderJpaRepository
                              -> OrderEventPublisher -> KafkaOrderEventPublisher -> KafkaTemplate

payments.events -> PaymentEventListener -> OrderService.applyPayment

OrderEntity (commerce.orders) 1 -> many OrderItemEntity (commerce.order_items)
```

Constructor injection is used throughout. A declared constructor dependency is a `depends_on` fact; it becomes a call edge only where a method is explicitly invoked.

## REST endpoints

The class-level path is the uniquely assigned constant `OrderController.BASE_PATH = "/api/orders"`. `STATUS_PATH` is another uniquely assigned static string.

| HTTP method | Full path | Handler |
| --- | --- | --- |
| `POST` | `/api/orders` | `OrderController.create(OrderRequest)` |
| `GET` | `/api/orders/{orderId}` | `OrderController.get(String)` |
| `GET` | `/api/orders` | `OrderController.list()` |
| `PATCH` | `/api/orders/{orderId}/status` | `OrderController.updateStatus(String, OrderStatusRequest)` |
| `GET`, `HEAD` | `/api/orders/readiness` | `OrderController.readiness()` |

Request-body validation, path variables, response status `201`, composed mapping annotations, and the multi-method mapping are intentional analysis targets.

## Expected static-analysis inventory

### Source units, types, and Java relationships

| Source/package | Important expected facts |
| --- | --- |
| `OrdersApplication.java` | application entrypoint; static `main(String[])` |
| `api` | records `OrderRequest`, nested `OrderRequest.Item`, `OrderResponse`, nested `ItemResponse`; `OrderController` |
| `application` | `OrderService`; `DefaultOrderService implements OrderService`; `OrderRepository` |
| `domain` | records `Order`, `OrderItem`; enum `OrderStatus`; exception class |
| `persistence` | JPA entities and `JpaOrderRepository implements OrderRepository` |
| `messaging` | `OrderEventPublisher`; Kafka publisher/listener; nested event records |
| `analysiscases.positive` | direct import, fully qualified reference, direct inheritance |

Expected `inherits_from`: `SpecialOrderNotFoundException -> OrderNotFoundException` and `OrderNotFoundException -> RuntimeException`. Expected `implements`: `DefaultOrderService -> OrderService`, `JpaOrderRepository -> OrderRepository`, and `KafkaOrderEventPublisher -> OrderEventPublisher`.

Overload identities must remain signature-qualified and distinct:

- `Order.create(String)`
- `Order.create(String, List<OrderItem>)`

The fixture also includes constructors, instance methods, static methods, enums, records, and nested static types (`Order.Summary` plus nested API/event records).

### Dependency injection and calls

| Consumer | Constructor dependency (`depends_on`) | Explicit important calls |
| --- | --- | --- |
| `OrderController` | `OrderService` | create/get/list/updateStatus |
| `DefaultOrderService` | `OrderRepository`, `OrderEventPublisher`, `OrderProperties` | repository find/save; publisher publish |
| `JpaOrderRepository` | `OrderJpaRepository` | JPA findById/save/list query |
| `KafkaOrderEventPublisher` | `KafkaTemplate<String,Object>` | `KafkaTemplate.send` |
| `PaymentEventListener` | `OrderService` | `OrderService.applyPayment` |

The two unannotated `AmbiguousServices.Gateway` implementations are diagnostic-only and must not resolve to an application injection target.

### Persistence resources and access

| DataResource identity | Mapping | Expected access |
| --- | --- | --- |
| `relational:commerce.orders` | `OrderEntity maps_to commerce.orders` | `JpaOrderRepository` reads and writes |
| `relational:commerce.order_items` | `OrderItemEntity maps_to commerce.order_items` | cascade reads and writes through order persistence |
| `relational:audit.orders` | identity-only `AuditOrderEntity` negative fixture outside runtime scan | must stay distinct from `commerce.orders`; no application read/write edge |

`OrderJpaRepository.findById`, `save`, `findAllByOrderByIdAsc`, and the static JPQL `findByStatus` are intentional. Column values, SQL parameters, entity payloads, and runtime native SQL are not expected graph facts.

### Kafka channels

| MessageChannel | Edge |
| --- | --- |
| `orders.events` | `KafkaOrderEventPublisher.publish` publishes via `KafkaTemplate.send` |
| `payments.events` | `PaymentEventListener.onPayment` consumes via `@KafkaListener` |

Topic constants are each assigned once in `MessagingTopics`. Payload fields, event bodies, payment references, Kafka bootstrap servers, and serializer details must not be persisted as graph facts.

### Configuration keys

Expected keys (names only) are:

- `spring.datasource.url` / `ORDERS_DATASOURCE_URL`
- `spring.datasource.username` / `ORDERS_DATASOURCE_USERNAME`
- `spring.datasource.password` / `ORDERS_DATASOURCE_PASSWORD`
- `spring.kafka.bootstrap-servers` / `ORDERS_KAFKA_BOOTSTRAP_SERVERS`
- `spring.kafka.listener.auto-startup`
- `orders.enabled` / `ORDERS_ENABLED`
- `orders.max-items` / `ORDERS_MAX_ITEMS`

No configuration value, connection string, bootstrap address, username, password, or raw exception containing configuration is expected in a graph or report.

## Intentional negative cases

| Fixture | Prohibited inference |
| --- | --- |
| `UnregisteredController` | no endpoint; class is not a component/controller bean |
| `DynamicPathController` | no guessed full endpoint path from `${fixture.dynamic-path}` |
| `DynamicTopicListener` | no guessed channel from a SpEL topic expression; class is not a component |
| `AmbiguousServices` | no chosen DI implementation and no invented call edge |
| `WildcardImportCase` and duplicate `Marker` classes | no guessed ambiguous simple-name target |
| `AuditOrderEntity` | never merge `audit.orders` with `commerce.orders`; no runtime access edge |
| `dynamic-native-query.java.fixture` | no inferred table/read edge from runtime SQL or non-literal table name |
| `syntax-error.java.fixture` | no normal source entity; syntax diagnostic only |

To build a dedicated syntax-error corpus, copy the content of `src/test/resources/analysis/syntax-error.java.fixture` to a `.java` file only on a separate fixture branch. Its inert extension intentionally keeps normal Maven builds valid.

The test-resource sentinel `RKG_TEST_SECRET_DO_NOT_PERSIST` must never appear in analyzer graphs, reports, or logs. The application does not log datasource/Kafka connection strings, payloads, or configuration values.
