package com.example.rkgfixture.orders.messaging;

import com.example.rkgfixture.orders.domain.Order;

public interface OrderEventPublisher {
    void publish(Order order);
}
