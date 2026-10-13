<script lang="ts">
import { defineComponent, type PropType } from 'vue'
import type { Order } from '#shared/types/order'
import OrderStatusBadge from './OrderStatusBadge.vue'

export default defineComponent({
  name: 'OrderCard',
  components: { OrderStatusBadge },
  props: {
    order: {
      type: Object as PropType<Order>,
      required: true,
    },
  },
  emits: {
    cancel: (orderId: string) => orderId.length > 0,
  },
  setup(props, { emit }) {
    const requestCancellation = () => emit('cancel', props.order.id)
    return { requestCancellation }
  },
})
</script>

<template>
  <article class="order-card">
    <h2><NuxtLink :to="`/orders/${order.id}`">Order {{ order.id }}</NuxtLink></h2>
    <p>{{ order.customerName }} · ${{ (order.totalCents / 100).toFixed(2) }}</p>
    <OrderStatusBadge :status="order.status" />
    <button v-if="order.status !== 'cancelled'" type="button" @click="requestCancellation">
      Cancel order
    </button>
  </article>
</template>

<style scoped>
.order-card { border: 1px solid #d1d5db; border-radius: 0.5rem; padding: 1rem; }
button { margin-left: 0.75rem; }
</style>
