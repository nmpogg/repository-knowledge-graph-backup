package com.example.rkgfixture.orders.messaging;
import static org.assertj.core.api.Assertions.assertThat;
import com.example.rkgfixture.orders.domain.OrderStatus;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
class EventContractTest {
 @Test void eventMatchesSharedContractExample() throws Exception {
  ObjectMapper mapper = new ObjectMapper();
  var expected = mapper.readTree(Files.readString(Path.of("../../contracts/examples/order-event.json")));
  var actual = mapper.valueToTree(new KafkaOrderEventPublisher.OrderEvent("order.updated", "order-1", OrderStatus.CREATED, "2026-10-05T10:00:00Z"));
  assertThat(actual).isEqualTo(expected);
 }
}
