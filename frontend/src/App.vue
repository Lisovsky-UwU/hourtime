<script setup lang="ts">
import { computed, watchEffect } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { TooltipProvider } from 'reka-ui'

import UiToastHost from '@/components/ui/UiToastHost.vue'
import { useDuration } from '@/composables/useDuration'
import AppLayout from '@/layouts/AppLayout.vue'
import AuthLayout from '@/layouts/AuthLayout.vue'
import { useTimerStore } from '@/stores/timer'

const route = useRoute()
const { t } = useI18n()
const timer = useTimerStore()
const showDuration = useDuration()

/**
 * A running timer takes over the tab title, clock first, so it reads even in
 * a narrow tab. Otherwise the title names the page.
 */
watchEffect(() => {
  const app = t('app.name')
  const running = timer.entry
  if (running) {
    document.title = `${showDuration(timer.elapsed)} - ${running.description || app}`
    return
  }
  const page = route.meta.titleKey
  document.title = page ? `${t(page)} - ${app}` : app
})

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
