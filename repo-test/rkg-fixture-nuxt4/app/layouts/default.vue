<script setup lang="ts">
const config = useRuntimeConfig()
</script>

<template>
  <div class="shell">
    <header>
      <strong>{{ config.public.portalName }}</strong>
      <nav aria-label="Primary navigation">
        <NuxtLink to="/">Home</NuxtLink>
        <NuxtLink to="/orders">Orders</NuxtLink>
        <NuxtLink to="/account/profile">Profile</NuxtLink>
      </nav>
      <ConnectionState />
    </header>
    <main>
      <slot />
    </main>
  </div>
</template>

<style scoped>
.shell { max-width: 60rem; margin: 0 auto; padding: 1rem; }
header { display: flex; gap: 1rem; align-items: center; }
nav { display: flex; gap: 0.75rem; }
</style>
