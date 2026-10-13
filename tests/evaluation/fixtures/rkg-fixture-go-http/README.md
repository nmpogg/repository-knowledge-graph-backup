# RKG fixture: Go HTTP routes

Analysis fixture for Gin, chi, and gorilla/mux. Source is never executed.

## Inventory

- `httpapi.GinHealth` handles `GET /health` on a Gin engine.
- `httpapi.ChiCatalog` handles `GET /orders` via the `OrdersPath` constant on a chi router.
- `httpapi.MuxShipment` handles `POST /shipments` on a gorilla/mux router.
- A concatenated Gin path is dynamic and must not become an endpoint.
- A suppressed path constant must not be stored.
