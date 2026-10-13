package com.example.rkgfixture.orders.messaging;

import static org.mockito.Mockito.verify;

import com.example.rkgfixture.orders.application.OrderService;
import com.example.rkgfixture.orders.domain.Order;
import com.example.rkgfixture.orders.domain.OrderStatus;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.kafka.core.KafkaTemplate;

import static org.mockito.Mockito.mock;

class KafkaMessagingTest {
    @Test
    void publisherSendsToOrdersTopic() {
        @SuppressWarnings("unchecked")
        KafkaTemplate<String, Object> template = mock(KafkaTemplate.class);
        KafkaOrderEventPublisher publisher = new KafkaOrderEventPublisher(template);
        Order order = new Order("order-3", List.of(), OrderStatus.CREATED);

        publisher.publish(order);

        verify(template).send(
                MessagingTopics.ORDERS_EVENTS,
                "order-3",
                new KafkaOrderEventPublisher.OrderEvent("order-3", OrderStatus.CREATED)
        );
    }

    @Test
    void listenerDelegatesPaymentToService() {
        OrderService service = mock(OrderService.class);
        PaymentEventListener listener = new PaymentEventListener(service);

        listener.onPayment(new PaymentEventListener.PaymentEvent("order-4", "payment-4"));

        verify(service).applyPayment("order-4");
    }
}
