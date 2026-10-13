package com.example.rkgfixture.orders.messaging;

import com.example.rkgfixture.orders.domain.Order;
import com.example.rkgfixture.orders.domain.OrderStatus;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

@Component
public class KafkaOrderEventPublisher implements OrderEventPublisher {
    private final KafkaTemplate<String, Object> kafkaTemplate;

    public KafkaOrderEventPublisher(KafkaTemplate<String, Object> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }

    @Override
    public void publish(Order order) {
        kafkaTemplate.send(
                MessagingTopics.ORDERS_EVENTS,
                order.id(),
                new OrderEvent(order.id(), order.status())
        );
    }

    public record OrderEvent(String orderId, OrderStatus status) {
    }
}
