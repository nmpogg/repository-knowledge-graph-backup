package com.example.rkgfixture.orders.application;

import com.example.rkgfixture.orders.domain.Order;
import com.example.rkgfixture.orders.domain.OrderItem;
import com.example.rkgfixture.orders.domain.OrderStatus;
import java.util.List;

public interface OrderService {
    Order createOrder(List<OrderItem> items);
    Order getOrder(String orderId);
    List<Order> listOrders();
    Order updateStatus(String orderId, OrderStatus status);
    Order applyPayment(String orderId);
}
