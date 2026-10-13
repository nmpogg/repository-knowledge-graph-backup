import { ref } from 'vue'
import type { Order } from '#shared/types/order'

export type OrdersFetcher = <T>(request: string, options?: { method?: string }) => Promise<T>

export function useOrders(fetcher: OrdersFetcher = $fetch) {
  const orders = ref<Order[]>([])
  const pending = ref(false)
  const error = ref<string | null>(null)

  async function load() {
    pending.value = true
    error.value = null
    try {
      orders.value = await fetcher<Order[]>('/api/orders')
    }
    catch {
      error.value = 'Unable to load orders'
    }
    finally {
      pending.value = false
    }
  }

  return { orders, pending, error, load }
}
