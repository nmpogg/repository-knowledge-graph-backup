import type { H3Event } from 'h3'
import { createError, defineEventHandler, getRouterParam } from 'h3'
import { orderService, type OrderService } from '../../../services/orderService'

type ParamReader = (event: H3Event, name: string) => string | undefined

export function createCancelOrderHandler(
  service: Pick<OrderService, 'cancelOrder'> = orderService,
  readParam: ParamReader = getRouterParam,
) {
  return async function cancelOrderHandler(event: H3Event) {
    const orderId = readParam(event, 'orderId')
    if (!orderId) throw createError({ statusCode: 400, statusMessage: 'orderId is required' })
    return service.cancelOrder(orderId)
  }
}

export default defineEventHandler(createCancelOrderHandler())
