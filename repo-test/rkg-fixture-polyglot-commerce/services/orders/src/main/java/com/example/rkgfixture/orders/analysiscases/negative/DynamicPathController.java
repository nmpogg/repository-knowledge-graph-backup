package com.example.rkgfixture.orders.analysiscases.negative;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;

// Expected: no guessed full path for the unresolved placeholder; this is not a registered bean.
@RequestMapping("${fixture.dynamic-path}")
public class DynamicPathController {
    @GetMapping("/status")
    public String dynamicStatus() {
        return "dynamic";
    }
}
