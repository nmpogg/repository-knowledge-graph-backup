package com.example.rkgfixture.orders.persistence;

import com.example.rkgfixture.orders.application.OrderRepository;
import com.example.rkgfixture.orders.domain.Order;
import java.util.List;
import java.util.Optional;
import org.springframework.stereotype.Repository;

@Repository
// RKG_EXPECT: orders-repository
public class JpaOrderRepository implements OrderRepository {
    private final OrderJpaRepository repository;

    public JpaOrderRepository(OrderJpaRepository repository) {
        this.repository = repository;
    }

    @Override
    public Order save(Order order) {
        return repository.save(OrderEntity.fromDomain(order)).toDomain();
    }

    @Override
    public Optional<Order> findById(String orderId) {
        return repository.findById(orderId).map(OrderEntity::toDomain);
    }

    @Override
    public List<Order> findAll() {
        return repository.findAllByOrderByIdAsc().stream().map(OrderEntity::toDomain).toList();
    }
}
