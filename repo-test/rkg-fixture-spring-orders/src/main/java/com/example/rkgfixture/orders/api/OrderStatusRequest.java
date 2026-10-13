package com.example.rkgfixture.orders.api;

import com.example.rkgfixture.orders.domain.OrderStatus;
import jakarta.validation.constraints.NotNull;

public record OrderStatusRequest(@NotNull OrderStatus status) {
}
