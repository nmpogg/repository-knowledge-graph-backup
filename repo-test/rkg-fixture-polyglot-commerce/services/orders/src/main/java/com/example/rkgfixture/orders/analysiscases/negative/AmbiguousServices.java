package com.example.rkgfixture.orders.analysiscases.negative;

// Expected: diagnostic only; two implementations are deliberately not Spring components.
public final class AmbiguousServices {
    private AmbiguousServices() {
    }

    public interface Gateway {
        String load(String id);
    }

    public static final class PrimaryGateway implements Gateway {
        @Override
        public String load(String id) { return "primary:" + id; }
    }

    public static final class SecondaryGateway implements Gateway {
        @Override
        public String load(String id) { return "secondary:" + id; }
    }
}
