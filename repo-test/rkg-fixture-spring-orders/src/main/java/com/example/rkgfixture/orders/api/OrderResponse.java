package com.example.rkgfixture.orders.api;

import com.example.rkgfixture.orders.domain.Order;
import com.example.rkgfixture.orders.domain.OrderStatus;
import java.util.List;

public record OrderResponse(
        String id,
        OrderStatus status,
        long totalCents,
        List<ItemResponse> items
) {
    public static OrderResponse from(Order order) {
        return new OrderResponse(
                order.id(),
                order.status(),
                order.totalCents(),
                order.items().stream()
                        .map(item -> new ItemResponse(item.sku(), item.quantity(), item.unitPriceCents()))
                        .toList()
        );
    }

    public record ItemResponse(String sku, int quantity, long unitPriceCents) {
    }
}
