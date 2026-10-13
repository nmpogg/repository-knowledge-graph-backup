<script setup lang="ts">
import type { Order } from '#shared/types/order'

definePageMeta({ title: 'Orders' })

const { orders, pending, error, load } = useOrders()

async function cancelOrder(order: Order) {
  await $fetch(`/api/orders/${order.id}/cancel`, { method: 'POST' })
  await load()
}

await load()
</script>

<template>
  <section>
    <h1>Orders</h1>
    <p v-if="pending">Loading orders…</p>
    <p v-else-if="error" role="alert">{{ error }}</p>
    <div v-else class="orders">
      <OrderCard
        v-for="order in orders"
        :key="order.id"
        :order="order"
        @cancel="cancelOrder(order)"
      />
    </div>
  </section>
</template>

<style scoped>
.orders { display: grid; gap: 1rem; }
</style>
