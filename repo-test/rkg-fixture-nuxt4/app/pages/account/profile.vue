<script setup lang="ts">
definePageMeta({
  title: 'Account profile',
  middleware: 'account',
  requiresAccount: true,
})
</script>

<template>
  <section>
    <h1>Account profile</h1>
    <p>Signed in as fixture.customer@example.test</p>
  </section>
</template>
