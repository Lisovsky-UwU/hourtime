<script setup lang="ts" generic="T extends string">
import { RadioGroupItem, RadioGroupRoot } from 'reka-ui'

import AppIcon from '@/components/AppIcon.vue'
import type { IconName } from '@/components/AppIcon.vue'

/**
 * A short choice shown all at once: theme, time format, a list filter.
 * Radio semantics, so arrow keys move between the options.
 */
const model = defineModel<T>({ required: true })

defineProps<{
  options: { value: T; label: string; icon?: IconName }[]
  /** Accessible name of the group. */
  label: string
  /** The labels are samples of numbers or times, set in `.num`. */
  numeric?: boolean
}>()
</script>

<template>
  <RadioGroupRoot
    :model-value="model"
    class="ui-segmented"
    orientation="horizontal"
    :aria-label="label"
    loop
    @update:model-value="(value) => (model = value as T)"
  >
    <RadioGroupItem
      v-for="option in options"
      :key="option.value"
      :value="option.value"
      class="ui-segmented-item"
      :class="{ num: numeric }"
    >
      <AppIcon v-if="option.icon" :name="option.icon" :size="16" />
      {{ option.label }}
    </RadioGroupItem>
  </RadioGroupRoot>
</template>

<style scoped>
.ui-segmented {
  display: inline-flex;
  flex: 0 0 auto;
  /* Wraps only when even its own width does not fit the screen. */
  flex-wrap: wrap;
  max-width: 100%;
  padding: 2px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--surface-muted);
}

.ui-segmented-item {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-width: 0;
  height: calc(var(--control-h) - 6px);
  padding: 0 12px;
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-muted);
  font: inherit;
  font-weight: 500;
  white-space: nowrap;
  cursor: pointer;
  transition:
    background-color var(--dur) var(--ease),
    color var(--dur) var(--ease);
}

.ui-segmented-item:hover {
  color: var(--text);
}

.ui-segmented-item[data-state='checked'] {
  background: var(--surface);
  color: var(--text);
  outline: 1px solid var(--border-strong);
  outline-offset: -1px;
}

.ui-segmented-item:focus-visible {
  outline: 2px solid var(--focus);
  outline-offset: -2px;
}
</style>
