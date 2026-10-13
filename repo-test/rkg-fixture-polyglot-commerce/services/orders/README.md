# Orders service
Java 21 / Spring Boot orders backend. The controller handles GET/POST `/api/orders`, GET `/api/orders/{orderId}`, PATCH `/api/orders/{orderId}/status`, and GET/HEAD readiness. It calls OrderService, implemented by DefaultOrderService; JPA persists `commerce.orders` and `commerce.order_items`; the Kafka publisher emits `orders.events` with the shared event envelope.

Run `./mvnw -o test` or `./mvnw -o verify` after dependencies and Maven Wrapper are cached. `pom.xml` pins Boot and plugin versions; `pom.sha256` detects manifest drift. Java 21 is enforced. Tests use Mockito, MockMvc and in-memory H2; no server, Kafka broker, PostgreSQL or external network is started. Kafka listener auto-start is disabled by default.

`analysiscases/negative/AuditOrderEntity` maps `audit.orders` outside the runtime entity scan; it must remain distinct from `commerce.orders`. Dynamic/unregistered controller/topic examples are analysis-only. Test logging is WARN and SQL/config/payload printing is disabled. Root syntax-error Java source is outside Maven source roots.
