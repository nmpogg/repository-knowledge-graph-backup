import { NestFactory } from "@nestjs/core";
import { AppModule } from "./app.module";
import { API_PREFIX } from "./constants";

export async function bootstrap(): Promise<void> {
  const app = await NestFactory.create(AppModule);
  app.setGlobalPrefix(API_PREFIX);
}
