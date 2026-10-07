<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { ToastProvider, ToastViewport } from 'reka-ui'

import UiToast from '@/components/ui/UiToast.vue'
import { toastManager } from '@/components/ui/toast'

/** Mounted once in App.vue; shows whatever `toast.*()` adds. */
const { t } = useI18n()
</script>

<template>
  <ToastProvider :toast-manager="toastManager" :label="t('ui.notification')" :limit="3">
    <ToastViewport class="ui-toast-viewport">
      <UiToast />
    </ToastViewport>
  </ToastProvider>
</template>

<style>
.ui-toast-viewport {
  position: fixed;
  z-index: 70;
  right: 16px;
  bottom: 16px;
  width: min(360px, calc(100vw - 32px));
  /* Toasts come newest first; the newest sits closest to the corner. */
  display: flex;
  flex-direction: column-reverse;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
  outline: none;
}
</style>
