package com.example.rkgfixture.orders.api;

import static org.mockito.ArgumentMatchers.anyList;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.head;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.patch;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.example.rkgfixture.orders.application.OrderService;
import com.example.rkgfixture.orders.domain.Order;
import com.example.rkgfixture.orders.domain.OrderItem;
import com.example.rkgfixture.orders.domain.OrderStatus;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(OrderController.class)
class OrderControllerTest {
    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private OrderService orderService;

    @Test
    void createsOrder() throws Exception {
        when(orderService.createOrder(anyList())).thenReturn(sampleOrder(OrderStatus.CREATED));

        mockMvc.perform(post("/api/orders")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"items":[{"sku":"SKU-1","quantity":2,"unitPriceCents":500}]}
                                """))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id").value("order-1"))
                .andExpect(jsonPath("$.totalCents").value(1000));

        verify(orderService).createOrder(anyList());
    }

    @Test
    void getsOrder() throws Exception {
        when(orderService.getOrder("order-1")).thenReturn(sampleOrder(OrderStatus.CREATED));

        mockMvc.perform(get("/api/orders/order-1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("CREATED"));
    }

    @Test
    void listsOrders() throws Exception {
        when(orderService.listOrders()).thenReturn(List.of(sampleOrder(OrderStatus.CREATED)));

        mockMvc.perform(get("/api/orders"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].id").value("order-1"));
    }

    @Test
    void updatesStatus() throws Exception {
        when(orderService.updateStatus("order-1", OrderStatus.SHIPPED))
                .thenReturn(sampleOrder(OrderStatus.SHIPPED));

        mockMvc.perform(patch("/api/orders/order-1/status")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"status\":\"SHIPPED\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("SHIPPED"));
    }

    @Test
    void supportsReadinessGetAndHead() throws Exception {
        mockMvc.perform(get("/api/orders/readiness"))
                .andExpect(status().isOk())
                .andExpect(content().string("ready"));
        mockMvc.perform(head("/api/orders/readiness"))
                .andExpect(status().isOk());
    }

    private static Order sampleOrder(OrderStatus status) {
        return new Order("order-1", List.of(new OrderItem("SKU-1", 2, 500)), status);
    }
}
