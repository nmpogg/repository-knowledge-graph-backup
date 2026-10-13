package com.example.rkgfixture.orders.analysiscases.positive;

import com.example.rkgfixture.orders.domain.Order;

public final class ResolutionCases {
    private ResolutionCases() {
    }

    public static String directImport(Order order) {
        return order.id();
    }

    public static String fullyQualifiedReference(
            com.example.rkgfixture.orders.analysiscases.negative.Marker marker
    ) {
        return marker.label();
    }
}
