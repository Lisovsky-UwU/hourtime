<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { TooltipProvider } from 'reka-ui'

import UiToastHost from '@/components/ui/UiToastHost.vue'
import AppLayout from '@/layouts/AppLayout.vue'
import AuthLayout from '@/layouts/AuthLayout.vue'

const route = useRoute()

const layout = computed(() => {
  if (route.meta.layout === 'app') return AppLayout
  if (route.meta.layout === 'auth') return AuthLayout
  return null
})
</script>

<template>
  <TooltipProvider :delay-duration="400">
    <component :is="layout" v-if="layout">
      <RouterView />
    </component>
    <RouterView v-else />
  </TooltipProvider>

  <UiToastHost />
</template>
