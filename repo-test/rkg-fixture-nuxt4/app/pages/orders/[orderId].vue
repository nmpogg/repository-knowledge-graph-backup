<script setup lang="ts">
import type { Order } from '#shared/types/order'

definePageMeta({ title: 'Order detail' })

const route = useRoute()
const orderId = computed(() => String(route.params.orderId))
const { data: order, error } = await useFetch<Order>(() => `/api/orders/${orderId.value}`)
</script>

<template>
  <section>
    <p><NuxtLink to="/orders">← All orders</NuxtLink></p>
    <p v-if="error" role="alert">Order could not be loaded.</p>
    <template v-else-if="order">
      <h1>Order {{ order.id }}</h1>
      <p>Customer: {{ order.customerName }}</p>
      <OrderStatusBadge :status="order.status" />
    </template>
  </section>
</template>
