package com.example.rkgfixture.analysiscases.negative;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

// Expected: distinct DataResource identity audit.orders; outside runtime entity/component scan.
@Entity(name = "AuditOrderEntity")
@Table(name = "orders", schema = "audit")
public class AuditOrderEntity {
    @Id
    private String id;

    protected AuditOrderEntity() {
    }
}
