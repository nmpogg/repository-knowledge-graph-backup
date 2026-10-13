import { Controller, EventPattern, Get, MessagePattern, Post } from "@nestjs/common";
import { CREATED, ORDERS } from "./constants";

@Controller(ORDERS)
export class OrdersController {
  @Get(":id")
  findOne(): void {}

  @Post()
  create(): void {}

  @MessagePattern(CREATED)
  onCreated(): void {}

  @EventPattern("order.shipped")
  onShipped(): void {}
}
