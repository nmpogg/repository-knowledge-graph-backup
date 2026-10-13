package com.example.rkgfixture.orders.persistence;

import com.example.rkgfixture.orders.domain.OrderStatus;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

public interface OrderJpaRepository extends JpaRepository<OrderEntity, String> {
    List<OrderEntity> findAllByOrderByIdAsc();

    @Query("select o from OrderEntity o where o.status = :status order by o.id")
    List<OrderEntity> findByStatus(OrderStatus status);
}
