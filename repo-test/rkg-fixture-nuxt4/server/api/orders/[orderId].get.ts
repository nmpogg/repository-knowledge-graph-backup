import type { H3Event } from 'h3'
import { createError, defineEventHandler, getRouterParam } from 'h3'
import { orderService, type OrderService } from '../../services/orderService'

type ParamReader = (event: H3Event, name: string) => string | undefined

export function createGetOrderHandler(
  service: Pick<OrderService, 'getOrder'> = orderService,
  readParam: ParamReader = getRouterParam,
) {
  return async function getOrderHandler(event: H3Event) {
    const orderId = readParam(event, 'orderId')
    if (!orderId) throw createError({ statusCode: 400, statusMessage: 'orderId is required' })
    return service.getOrder(orderId)
  }
}

export default defineEventHandler(createGetOrderHandler())
