<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import {
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogOverlay,
  DialogPortal,
  DialogRoot,
  DialogTitle,
} from 'reka-ui'

import AppIcon from '@/components/AppIcon.vue'

const open = defineModel<boolean>('open', { default: false })

withDefaults(defineProps<{ title: string; description?: string }>(), { description: undefined })

const { t } = useI18n()
</script>

<template>
  <DialogRoot v-model:open="open">
    <DialogPortal>
      <DialogOverlay class="ui-dialog-overlay" />
      <!-- Esc and the explicit buttons close it; a stray click outside must not
           throw away what the user typed. Without a description the
           aria-describedby attribute must go, or it points at nothing. -->
      <DialogContent
        class="ui-dialog"
        v-bind="description ? {} : { 'aria-describedby': undefined }"
        @interact-outside.prevent
      >
        <DialogTitle class="ui-dialog-title">{{ title }}</DialogTitle>
        <DialogDescription v-if="description" class="ui-dialog-description">
          {{ description }}
        </DialogDescription>

        <div v-if="$slots.default" class="ui-dialog-body">
          <slot :close="() => (open = false)" />
        </div>

        <footer v-if="$slots.footer" class="ui-dialog-footer">
          <slot name="footer" :close="() => (open = false)" />
        </footer>

        <!-- Last in the DOM so the dialog opens with focus on the first field,
             not on the close button. -->
        <DialogClose class="ui-dialog-close" :aria-label="t('common.close')">
          <AppIcon name="close" :size="18" />
        </DialogClose>
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>

<style>
/* Global: rendered in a portal. */
.ui-dialog-overlay {
  position: fixed;
  inset: 0;
  z-index: 40;
  background: var(--overlay);
}

.ui-dialog-overlay[data-state='open'] {
  animation: ui-fade-in var(--dur) var(--ease);
}

.ui-dialog {
  position: fixed;
  z-index: 41;
  top: 50%;
  left: 50%;
  translate: -50% -50%;
  width: min(460px, calc(100vw - 32px));
  max-height: calc(100dvh - 32px);
  overflow: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sheet);
  background: var(--surface);
  color: var(--text);
  box-shadow: var(--shadow-float);
}

.ui-dialog[data-state='open'] {
  animation: ui-float-in var(--dur) var(--ease);
}

.ui-dialog:focus-visible {
  outline: none;
}

.ui-dialog-title {
  margin: 0;
  padding-right: 32px;
  font-size: var(--text-lg);
  font-weight: 600;
}

.ui-dialog-close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  position: absolute;
  top: 14px;
  right: 14px;
  width: 30px;
  height: 30px;
  padding: 0;
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
}

.ui-dialog-close:hover {
  background: var(--surface-muted);
  color: var(--text);
}

.ui-dialog-description {
  margin: -4px 0 0;
  color: var(--text-muted);
}

.ui-dialog-body {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.ui-dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding-top: 4px;
}
</style>
