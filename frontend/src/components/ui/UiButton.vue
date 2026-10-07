<script setup lang="ts">
import AppIcon from '@/components/AppIcon.vue'
import type { IconName } from '@/components/AppIcon.vue'

withDefaults(
  defineProps<{
    /** `danger-solid` is for the final "yes" of an irreversible action only. */
    variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'danger-solid'
    size?: 'sm' | 'md'
    type?: 'button' | 'submit'
    icon?: IconName
  }>(),
  { variant: 'secondary', size: 'md', type: 'button', icon: undefined },
)
</script>

<template>
  <button :type="type" class="ui-button" :data-variant="variant" :data-size="size">
    <AppIcon v-if="icon" :name="icon" :size="size === 'sm' ? 14 : 16" />
    <slot />
  </button>
</template>

<style scoped>
.ui-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: var(--control-h);
  padding: 0 14px;
  border: 1px solid transparent;
  border-radius: var(--radius);
  font: inherit;
  font-weight: 500;
  white-space: nowrap;
  cursor: pointer;
  transition:
    background-color var(--dur) var(--ease),
    border-color var(--dur) var(--ease),
    color var(--dur) var(--ease);
}

.ui-button[data-size='sm'] {
  height: var(--control-h-sm);
  padding: 0 10px;
  font-size: var(--text-xs);
}

.ui-button[data-variant='primary'] {
  background: var(--accent);
  color: var(--accent-contrast);
}

.ui-button[data-variant='primary']:hover:not(:disabled) {
  background: var(--accent-hover);
}

.ui-button[data-variant='secondary'] {
  background: var(--surface);
  border-color: var(--border);
  color: var(--text);
}

.ui-button[data-variant='secondary']:hover:not(:disabled) {
  border-color: var(--border-strong);
  background: var(--surface-muted);
}

.ui-button[data-variant='ghost'] {
  background: transparent;
  color: var(--text-muted);
}

.ui-button[data-variant='ghost']:hover:not(:disabled) {
  background: var(--surface-muted);
  color: var(--text);
}

.ui-button[data-variant='danger'] {
  background: var(--surface);
  border-color: var(--border);
  color: var(--danger);
}

.ui-button[data-variant='danger']:hover:not(:disabled) {
  border-color: var(--danger);
  background: var(--danger-soft);
}

.ui-button[data-variant='danger-solid'] {
  background: var(--danger);
  color: var(--danger-contrast);
}

.ui-button[data-variant='danger-solid']:hover:not(:disabled) {
  background: color-mix(in srgb, var(--danger) 88%, var(--text));
}

.ui-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
