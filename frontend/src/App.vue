<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { TooltipProvider } from 'reka-ui'

import UiToastHost from '@/components/ui/UiToastHost.vue'
import AppLayout from '@/layouts/AppLayout.vue'

const route = useRoute()

const layout = computed(() => (route.meta.layout === 'app' ? AppLayout : null))
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
