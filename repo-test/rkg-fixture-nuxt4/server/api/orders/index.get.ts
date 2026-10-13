import type { H3Event } from 'h3'
import { defineEventHandler } from 'h3'
import { orderService, type OrderService } from '../../services/orderService'

export function createListOrdersHandler(service: Pick<OrderService, 'listOrders'> = orderService) {
  return async function listOrdersHandler(_event: H3Event) {
    return service.listOrders()
  }
}

export default defineEventHandler(createListOrdersHandler())
