<template>
  <router-view />
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import router from './router';

onMounted(() => {
  const userToken = localStorage.getItem("userToken")
  if (userToken === null) {
    router.push("/login")
  }
})
</script>
