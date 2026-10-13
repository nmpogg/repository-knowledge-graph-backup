package com.example.rkgfixture.orders.domain;

public record OrderItem(String sku, int quantity, long unitPriceCents) {
    public OrderItem {
        if (sku == null || sku.isBlank()) {
            throw new IllegalArgumentException("sku is required");
        }
        if (quantity < 1 || unitPriceCents < 0) {
            throw new IllegalArgumentException("quantity and price must be valid");
        }
    }

    public long subtotalCents() {
        return Math.multiplyExact(quantity, unitPriceCents);
    }
}
