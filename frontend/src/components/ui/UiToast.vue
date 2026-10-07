<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { ToastClose, ToastDescription, ToastRoot, ToastTitle, useToastManager } from 'reka-ui'

import AppIcon from '@/components/AppIcon.vue'

/** The toasts themselves; must sit inside the ToastProvider of UiToastHost. */
const { toasts } = useToastManager()
const { t } = useI18n()
</script>

<template>
  <ToastRoot v-for="item in toasts" :key="item.id" :toast="item" class="ui-toast">
    <AppIcon
      :name="item.status === 'error' ? 'alert' : item.status === 'success' ? 'check' : 'info'"
      :size="18"
      class="ui-toast-icon"
    />
    <div class="ui-toast-text">
      <ToastTitle class="ui-toast-title" />
      <ToastDescription class="ui-toast-description" />
    </div>
    <ToastClose class="ui-toast-close" :aria-label="t('common.close')">
      <AppIcon name="close" :size="16" />
    </ToastClose>
  </ToastRoot>
</template>

<style>
.ui-toast {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 12px 12px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--surface);
  color: var(--text);
  box-shadow: var(--shadow-float);
}

.ui-toast[data-limited] {
  display: none;
}

.ui-toast[data-state='open'] {
  animation: ui-toast-in 200ms var(--ease);
}

.ui-toast[data-state='closed'] {
  animation: ui-toast-out 120ms var(--ease) forwards;
}

.ui-toast[data-swipe='move'] {
  translate: var(--reka-toast-swipe-move-x) 0;
}

.ui-toast[data-swipe='cancel'] {
  translate: 0 0;
  transition: translate var(--dur) var(--ease);
}

.ui-toast[data-swipe='end'] {
  animation: ui-toast-swipe-out 120ms var(--ease) forwards;
}

.ui-toast-icon {
  flex: 0 0 auto;
  margin-top: 1px;
  color: var(--text-muted);
}

.ui-toast[data-status='error'] {
  border-color: color-mix(in srgb, var(--danger) 45%, var(--border));
}

.ui-toast[data-status='error'] .ui-toast-icon {
  color: var(--danger);
}

.ui-toast[data-status='success'] .ui-toast-icon {
  color: var(--success);
}

.ui-toast-text {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.ui-toast-title {
  font-weight: 500;
}

.ui-toast-description {
  color: var(--text-muted);
}

.ui-toast-close {
  display: inline-flex;
  flex: 0 0 auto;
  padding: 2px;
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
}

.ui-toast-close:hover {
  background: var(--surface-muted);
  color: var(--text);
}

@keyframes ui-toast-in {
  from {
    opacity: 0;
    translate: 0 8px;
  }
}

@keyframes ui-toast-out {
  to {
    opacity: 0;
  }
}

@keyframes ui-toast-swipe-out {
  from {
    translate: var(--reka-toast-swipe-end-x) 0;
  }

  to {
    translate: 100% 0;
    opacity: 0;
  }
}
</style>
