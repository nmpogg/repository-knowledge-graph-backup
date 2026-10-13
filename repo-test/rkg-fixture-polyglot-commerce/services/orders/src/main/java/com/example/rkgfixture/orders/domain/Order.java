package com.example.rkgfixture.orders.domain;

import java.util.List;

public record Order(String id, List<OrderItem> items, OrderStatus status) {
    public Order {
        items = List.copyOf(items);
    }

    public static Order create(String id, List<OrderItem> items) {
        return new Order(id, items, OrderStatus.CREATED);
    }

    public static Order create(String id) {
        return create(id, List.of());
    }

    public long totalCents() {
        return items.stream().mapToLong(OrderItem::subtotalCents).sum();
    }

    public Order withStatus(OrderStatus newStatus) {
        return new Order(id, items, newStatus);
    }

    public static final class Summary {
        private final String id;
        private final long totalCents;

        public Summary(String id, long totalCents) {
            this.id = id;
            this.totalCents = totalCents;
        }

        public String id() { return id; }
        public long totalCents() { return totalCents; }
    }
}
