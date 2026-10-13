package com.example.rkgfixture.orders.persistence;

import com.example.rkgfixture.orders.domain.OrderItem;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;

@Entity
@Table(name = "order_items", schema = "commerce")
public class OrderItemEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "order_id", nullable = false)
    private OrderEntity order;

    private String sku;
    private int quantity;
    private long unitPriceCents;

    protected OrderItemEntity() {
    }

    private OrderItemEntity(OrderEntity order, String sku, int quantity, long unitPriceCents) {
        this.order = order;
        this.sku = sku;
        this.quantity = quantity;
        this.unitPriceCents = unitPriceCents;
    }

    public static OrderItemEntity fromDomain(OrderEntity order, OrderItem item) {
        return new OrderItemEntity(order, item.sku(), item.quantity(), item.unitPriceCents());
    }

    public OrderItem toDomain() {
        return new OrderItem(sku, quantity, unitPriceCents);
    }
}
