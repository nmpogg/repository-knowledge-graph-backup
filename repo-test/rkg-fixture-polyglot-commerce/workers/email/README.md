# Email worker
BullMQ consumer for `order-email`. The application boundary `dispatchOrderEvent(topic,event,queue)` receives a delivered `orders.events` envelope and calls `enqueueOrderEmail`; the worker processor calls `EmailService.sendOrderEmail`. The delivery boundary is injected, not a built-in Kafka subscriber. EmailService is an intentional no-network stub.

`src/index.ts` exports explicit bootstrap; `src/main.ts` calls it only when invoked as the entrypoint. Imports neither connect to Redis nor install signal handlers. Runtime keys are `REDIS_URL` and `EMAIL_FROM`; config values and job payloads are never logged.

Install `npm ci`, then `npm run lint`, `npm test`, `npm run typecheck`, `npm run build`. `package-lock.json` pins dependencies. Tests use fake queues/services and import-side-effect guards, so no Redis, SMTP or network is required. `src/analysis-cases/negative` contains a dynamic queue and a shadowed BullMQ constructor.
