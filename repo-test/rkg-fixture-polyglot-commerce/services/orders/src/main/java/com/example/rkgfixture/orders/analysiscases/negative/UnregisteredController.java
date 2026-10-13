package com.example.rkgfixture.orders.analysiscases.negative;

import org.springframework.web.bind.annotation.GetMapping;

// Expected: no exposed endpoint because this class is not a controller or registered bean.
public class UnregisteredController {
    @GetMapping("/internal/unregistered")
    public String hidden() {
        return "hidden";
    }
}
