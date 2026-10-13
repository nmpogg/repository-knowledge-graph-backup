package com.example.rkgfixture.orders.persistence;

import static org.assertj.core.api.Assertions.assertThat;

import com.example.rkgfixture.orders.domain.Order;
import com.example.rkgfixture.orders.domain.OrderItem;
import com.example.rkgfixture.orders.domain.OrderStatus;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.boot.test.autoconfigure.jdbc.AutoConfigureTestDatabase;
import org.springframework.context.annotation.Import;

@DataJpaTest(showSql = false, properties = {
        "spring.datasource.url=jdbc:h2:mem:jpa-test;MODE=PostgreSQL;INIT=CREATE SCHEMA IF NOT EXISTS commerce",
        "spring.jpa.hibernate.ddl-auto=create-drop"
})
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
@Import(JpaOrderRepository.class)
class JpaOrderRepositoryTest {
    @Autowired
    private JpaOrderRepository repository;

    @Autowired
    private OrderJpaRepository jpaRepository;

    @Test
    void mapsWritesAndReadsCommerceTables() {
        Order order = new Order(
                "order-b",
                List.of(new OrderItem("SKU-2", 2, 450)),
                OrderStatus.CREATED
        );

        repository.save(order);

        assertThat(repository.findById("order-b")).contains(order);
        assertThat(repository.findAll()).extracting(Order::id).containsExactly("order-b");
        assertThat(jpaRepository.findByStatus(OrderStatus.CREATED)).hasSize(1);
    }
}
