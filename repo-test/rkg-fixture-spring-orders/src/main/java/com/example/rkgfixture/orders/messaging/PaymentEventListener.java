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
    public void onPayment(PaymentEvent event) {
        orderService.applyPayment(event.orderId());
    }

    public record PaymentEvent(String orderId, String paymentReference) {
    }
}
