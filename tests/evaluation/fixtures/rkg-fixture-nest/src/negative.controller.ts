import { Controller, Get, MessagePattern } from "@nestjs/common";

const runtimePrefix = "audit" + "/dyn";

@Controller(runtimePrefix)
export class DynamicController {
  @Get("items")
  list(): void {}
}

@Controller("audit")
export class AuditController {
  @Get("health")
  health(): void {}

  @Get(runtimePrefix)
  search(): void {}

  @MessagePattern(runtimePrefix)
  onRuntime(): void {}
}
