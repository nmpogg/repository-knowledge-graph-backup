<script setup lang="ts">
import type { OrderStatus } from '#shared/types/order'

defineProps<{
  status: OrderStatus
}>()
</script>

<template>
  <span class="badge" :data-status="status">{{ status }}</span>
</template>

<style scoped>
.badge { padding: 0.15rem 0.5rem; border: 1px solid currentColor; border-radius: 999px; }
</style>
