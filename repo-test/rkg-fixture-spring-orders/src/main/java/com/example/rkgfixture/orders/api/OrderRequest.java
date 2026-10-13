package com.example.rkgfixture.orders.api;

import com.example.rkgfixture.orders.domain.OrderItem;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import java.util.List;

public record OrderRequest(@NotEmpty List<@Valid Item> items) {
    public List<OrderItem> toDomainItems() {
        return items.stream()
                .map(item -> new OrderItem(item.sku(), item.quantity(), item.unitPriceCents()))
                .toList();
    }

    public record Item(
            @NotBlank String sku,
            @Min(1) int quantity,
            @NotNull @Min(0) Long unitPriceCents
    ) {
    }
}
