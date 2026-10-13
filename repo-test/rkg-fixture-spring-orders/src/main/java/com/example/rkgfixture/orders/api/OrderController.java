package com.example.rkgfixture.orders.api;

import static org.springframework.http.HttpStatus.CREATED;

import com.example.rkgfixture.orders.application.OrderService;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping(OrderController.BASE_PATH)
public class OrderController {
    public static final String BASE_PATH = "/api/orders";
    public static final String STATUS_PATH = "/{orderId}/status";

    private final OrderService orderService;

    public OrderController(OrderService orderService) {
        this.orderService = orderService;
    }

    @PostMapping(consumes = MediaType.APPLICATION_JSON_VALUE)
    @ResponseStatus(CREATED)
    public OrderResponse create(@Valid @RequestBody OrderRequest request) {
        return OrderResponse.from(orderService.createOrder(request.toDomainItems()));
    }

    @GetMapping("/{orderId}")
    public OrderResponse get(@PathVariable String orderId) {
        return OrderResponse.from(orderService.getOrder(orderId));
    }

    @GetMapping
    public List<OrderResponse> list() {
        return orderService.listOrders().stream().map(OrderResponse::from).toList();
    }

    @PatchMapping(path = STATUS_PATH, consumes = MediaType.APPLICATION_JSON_VALUE)
    public OrderResponse updateStatus(
            @PathVariable String orderId,
            @Valid @RequestBody OrderStatusRequest request
    ) {
        return OrderResponse.from(orderService.updateStatus(orderId, request.status()));
    }

    @RequestMapping(path = "/readiness", method = {RequestMethod.GET, RequestMethod.HEAD})
    public String readiness() {
        return "ready";
    }
}
