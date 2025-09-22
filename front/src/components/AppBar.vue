<template>
  <div class="bg-bg-dark w-full p-5 flex items-center gap-4 h-[60px]">
    <Logo />
    <div class="flex-grow" />
    <OrganizationSelector />
  </div>
</template>

<script setup lang="ts">
import { useUserData } from '@/stores/user-data';
import OrganizationSelector from './organization/OrganizationSelector.vue';
import Logo from './ui/Logo.vue';
import { ref } from 'vue';

const logoutLoading = ref(false)
const userData = useUserData()

async function logout() {
  logoutLoading.value = true
  try {
    await userData.logout()
  } finally {
    logoutLoading.value = false
  }
}
</script>
