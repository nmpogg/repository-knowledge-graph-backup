package com.example.rkgfixture.orders.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebMvcConfig implements WebMvcConfigurer {
    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry
                .addInterceptor(new OrderAuditInterceptor())
                .addPathPatterns("/api/orders/{orderId}")
                .order(2);
    }
}
