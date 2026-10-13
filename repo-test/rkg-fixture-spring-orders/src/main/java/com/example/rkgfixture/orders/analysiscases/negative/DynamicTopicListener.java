package com.example.rkgfixture.orders.analysiscases.negative;

import org.springframework.kafka.annotation.KafkaListener;

// Expected: diagnostic only; no MessageChannel identity guessed from this expression.
public class DynamicTopicListener {
    @KafkaListener(topics = "#{systemProperties['fixture.topic']}")
    public void onDynamicTopic(String ignoredPayload) {
        // Intentionally no-op and not a Spring component.
    }
}
