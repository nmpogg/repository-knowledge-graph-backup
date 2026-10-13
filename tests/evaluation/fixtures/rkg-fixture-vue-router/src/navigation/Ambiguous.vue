<script setup lang="ts">
// RKG_TEST_SECRET_DO_NOT_PERSIST
import { useRouter } from "vue-router";

export function openAmbiguous(target: string) {
  const router = useRouter();
  router.push(target);
}
</script>

<template>
  <p>ambiguous</p>
</template>
