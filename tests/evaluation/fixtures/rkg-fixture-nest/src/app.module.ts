import { Module } from "@nestjs/common";
import { RouterModule } from "@nestjs/core";
import { SHOP } from "./constants";
import { OrdersModule } from "./orders.module";

@Module({
  imports: [RouterModule.register([{ path: SHOP, module: OrdersModule }])],
})
export class AppModule {}
