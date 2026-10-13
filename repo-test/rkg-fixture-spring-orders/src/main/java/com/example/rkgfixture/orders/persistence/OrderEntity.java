package com.example.rkgfixture.orders.persistence;

import com.example.rkgfixture.orders.domain.Order;
import com.example.rkgfixture.orders.domain.OrderStatus;
import jakarta.persistence.CascadeType;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Id;
import jakarta.persistence.OneToMany;
import jakarta.persistence.Table;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "orders", schema = "commerce")
public class OrderEntity {
    @Id
    private String id;

    @Enumerated(EnumType.STRING)
    private OrderStatus status;

    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL, orphanRemoval = true)
    private final List<OrderItemEntity> items = new ArrayList<>();

    protected OrderEntity() {
    }

    public OrderEntity(String id, OrderStatus status) {
        this.id = id;
        this.status = status;
    }

    public static OrderEntity fromDomain(Order order) {
        OrderEntity entity = new OrderEntity(order.id(), order.status());
        order.items().forEach(item -> entity.items.add(OrderItemEntity.fromDomain(entity, item)));
        return entity;
    }

    public Order toDomain() {
        return new Order(id, items.stream().map(OrderItemEntity::toDomain).toList(), status);
    }

    public String getId() { return id; }
    public OrderStatus getStatus() { return status; }
    public List<OrderItemEntity> getItems() { return List.copyOf(items); }
}
