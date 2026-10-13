package com.example.rkgfixture.orders;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest(properties = "spring.kafka.listener.auto-startup=false")
class OrdersApplicationTest {
    @Test
    void contextLoadsWithoutExternalInfrastructure() {
    }
}
