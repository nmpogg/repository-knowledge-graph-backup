import express, { Router } from "express";
import { ORDERS_PATH } from "./constants";
import { createOrder, listOrders, removeOrder } from "./handlers";

const app = express();
const router = Router();

function healthCheck(): void {}

function requestLogger(): void {}

app.get("/health", healthCheck);
app.get(ORDERS_PATH, listOrders);
app.post("/orders", createOrder);
router.delete("/orders/:id", removeOrder);
app.put("/orders/:id", (_req: unknown, _res: unknown) => {});
app.use(requestLogger);
