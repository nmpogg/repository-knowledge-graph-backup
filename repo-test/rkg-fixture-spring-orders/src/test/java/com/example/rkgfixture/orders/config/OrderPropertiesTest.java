package com.example.rkgfixture.orders.config;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.boot.test.context.runner.ApplicationContextRunner;
import org.springframework.context.annotation.Configuration;

class OrderPropertiesTest {
    private final ApplicationContextRunner runner = new ApplicationContextRunner()
            .withUserConfiguration(PropertiesConfiguration.class)
            .withPropertyValues("orders.enabled=false", "orders.max-items=25");

    @Test
    void bindsServiceOptions() {
        runner.run(context -> {
            assertThat(context).hasSingleBean(OrderProperties.class);
            assertThat(context.getBean(OrderProperties.class))
                    .isEqualTo(new OrderProperties(false, 25));
        });
    }

    @Configuration(proxyBeanMethods = false)
    @EnableConfigurationProperties(OrderProperties.class)
    static class PropertiesConfiguration {
    }
}
