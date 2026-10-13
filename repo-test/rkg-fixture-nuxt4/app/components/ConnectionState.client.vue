<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'

const online = ref(true)
const update = () => { online.value = navigator.onLine }

onMounted(() => {
  update()
  window.addEventListener('online', update)
  window.addEventListener('offline', update)
})

onBeforeUnmount(() => {
  window.removeEventListener('online', update)
  window.removeEventListener('offline', update)
})
</script>

<template>
  <small role="status">{{ online ? 'Online' : 'Offline' }}</small>
</template>
