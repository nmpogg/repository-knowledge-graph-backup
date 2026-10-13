package com.example.rkgfixture.orders.analysiscases.positive;

import com.example.rkgfixture.orders.domain.OrderNotFoundException;

public class SpecialOrderNotFoundException extends OrderNotFoundException {
    public SpecialOrderNotFoundException(String orderId) {
        super(orderId);
    }
}
