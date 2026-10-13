package com.example.rkgfixture.orders.analysiscases.negative;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.HandlerInterceptor;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class DynamicInterceptorConfig implements WebMvcConfigurer {
    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        HandlerInterceptor selected = select();
        registry.addInterceptor(selected).addPathPatterns("/api/orders/{orderId}");
    }

    private HandlerInterceptor select() {
        return null;
    }
}
