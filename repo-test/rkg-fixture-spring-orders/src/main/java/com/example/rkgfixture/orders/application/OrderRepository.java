package com.example.rkgfixture.orders.application;

import com.example.rkgfixture.orders.domain.Order;
import java.util.List;
import java.util.Optional;

public interface OrderRepository {
    Order save(Order order);
    Optional<Order> findById(String orderId);
    List<Order> findAll();
}
