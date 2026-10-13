package com.example.rkgfixture.orders.config;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.validation.annotation.Validated;

@Validated
@ConfigurationProperties(prefix = "orders")
public record OrderProperties(
        boolean enabled,
        @Min(1) @Max(500) int maxItems
) {
}
