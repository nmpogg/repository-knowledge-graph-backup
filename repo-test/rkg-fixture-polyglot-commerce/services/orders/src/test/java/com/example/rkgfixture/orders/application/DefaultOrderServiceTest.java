package com.example.rkgfixture.orders.application;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.example.rkgfixture.orders.config.OrderProperties;
import com.example.rkgfixture.orders.domain.Order;
import com.example.rkgfixture.orders.domain.OrderItem;
import com.example.rkgfixture.orders.domain.OrderNotFoundException;
import com.example.rkgfixture.orders.domain.OrderStatus;
import com.example.rkgfixture.orders.messaging.OrderEventPublisher;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class DefaultOrderServiceTest {
    @Mock
    private OrderRepository repository;
    @Mock
    private OrderEventPublisher publisher;

    private DefaultOrderService service;

    @BeforeEach
    void setUp() {
        service = new DefaultOrderService(repository, publisher, new OrderProperties(true, 10));
    }

    @Test
    void createsPersistsAndPublishesOrder() {
        when(repository.save(any(Order.class))).thenAnswer(invocation -> invocation.getArgument(0));
        List<OrderItem> items = List.of(new OrderItem("SKU-1", 1, 700));

        Order result = service.createOrder(items);

        assertThat(result.status()).isEqualTo(OrderStatus.CREATED);
        verify(repository).save(any(Order.class));
        verify(publisher).publish(result);
    }

    @Test
    void updatesStatusAndPublishes() {
        Order current = Order.create("order-2", List.of());
        when(repository.findById("order-2")).thenReturn(Optional.of(current));
        when(repository.save(any(Order.class))).thenAnswer(invocation -> invocation.getArgument(0));

        Order result = service.updateStatus("order-2", OrderStatus.PROCESSING);

        assertThat(result.status()).isEqualTo(OrderStatus.PROCESSING);
        verify(publisher).publish(result);
    }

    @Test
    void reportsMissingOrder() {
        when(repository.findById("missing")).thenReturn(Optional.empty());
        assertThatThrownBy(() -> service.getOrder("missing"))
                .isInstanceOf(OrderNotFoundException.class);
    }
}
