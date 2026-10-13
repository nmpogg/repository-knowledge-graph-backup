import express from "express";
import { listOrders } from "./handlers";

const app = express();
const dynamicPath = "/items/" + "x";

app.get(dynamicPath, listOrders);
