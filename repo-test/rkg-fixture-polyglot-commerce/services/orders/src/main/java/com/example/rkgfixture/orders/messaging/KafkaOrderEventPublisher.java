package com.example.rkgfixture.orders.messaging;
import com.example.rkgfixture.orders.domain.Order;
import com.example.rkgfixture.orders.domain.OrderStatus;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.Clock;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;
@Component
public class KafkaOrderEventPublisher implements OrderEventPublisher {
    private final KafkaTemplate<String, Object> kafkaTemplate;
    private final Clock clock;
    @org.springframework.beans.factory.annotation.Autowired
    public KafkaOrderEventPublisher(KafkaTemplate<String, Object> kafkaTemplate) {
        this(kafkaTemplate, Clock.systemUTC());
    }
    KafkaOrderEventPublisher(KafkaTemplate<String, Object> kafkaTemplate, Clock clock) {
        this.kafkaTemplate = kafkaTemplate; this.clock = clock;
    }
    // RKG_EXPECT: spring-publish-orders
    @Override public void publish(Order order) {
        kafkaTemplate.send(MessagingTopics.ORDERS_EVENTS, order.id(),
                new OrderEvent("order.updated", order.id(), order.status(), clock.instant().toString()));
    }
    public record OrderEvent(String type, @JsonProperty("order_id") String orderId,
            OrderStatus status, @JsonProperty("occurred_at") String occurredAt) {}
}
