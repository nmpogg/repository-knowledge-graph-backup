package com.example.rkgfixture.orders.application;

import com.example.rkgfixture.orders.config.OrderProperties;
import com.example.rkgfixture.orders.domain.Order;
import com.example.rkgfixture.orders.domain.OrderItem;
import com.example.rkgfixture.orders.domain.OrderNotFoundException;
import com.example.rkgfixture.orders.domain.OrderStatus;
import com.example.rkgfixture.orders.messaging.OrderEventPublisher;
import java.util.List;
import java.util.UUID;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional
public class DefaultOrderService implements OrderService {
    private final OrderRepository repository;
    private final OrderEventPublisher eventPublisher;
    private final OrderProperties properties;

    public DefaultOrderService(
            OrderRepository repository,
            OrderEventPublisher eventPublisher,
            OrderProperties properties
    ) {
        this.repository = repository;
        this.eventPublisher = eventPublisher;
        this.properties = properties;
    }

    @Override
    public Order createOrder(List<OrderItem> items) {
        if (!properties.enabled()) {
            throw new IllegalStateException("Order creation is disabled");
        }
        if (items.size() > properties.maxItems()) {
            throw new IllegalArgumentException("Order has too many items");
        }
        Order order = Order.create(UUID.randomUUID().toString(), items);
        Order saved = repository.save(order);
        eventPublisher.publish(saved);
        return saved;
    }

    @Override
    @Transactional(readOnly = true)
    public Order getOrder(String orderId) {
        return repository.findById(orderId)
                .orElseThrow(() -> new OrderNotFoundException(orderId));
    }

    @Override
    @Transactional(readOnly = true)
    public List<Order> listOrders() {
        return repository.findAll();
    }

    @Override
    public Order updateStatus(String orderId, OrderStatus status) {
        Order updated = getOrder(orderId).withStatus(status);
        Order saved = repository.save(updated);
        eventPublisher.publish(saved);
        return saved;
    }

    @Override
    public Order applyPayment(String orderId) {
        return updateStatus(orderId, OrderStatus.PAID);
    }
}
