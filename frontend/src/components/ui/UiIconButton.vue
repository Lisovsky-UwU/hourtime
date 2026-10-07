<script setup lang="ts">
import AppIcon from '@/components/AppIcon.vue'
import type { IconName } from '@/components/AppIcon.vue'
import UiTooltip from '@/components/ui/UiTooltip.vue'

/**
 * A button that is only an icon. `label` is mandatory: it is the accessible
 * name and the tooltip, since the glyph alone does not say what happens.
 */
// The root is the tooltip wrapper; listeners and attrs belong on the button.
defineOptions({ inheritAttrs: false })

withDefaults(
  defineProps<{
    icon: IconName
    label: string
    variant?: 'ghost' | 'secondary' | 'danger'
    size?: 'sm' | 'md'
    type?: 'button' | 'submit'
    /** Off for menu triggers: two popups on one element fight over it. */
    tooltip?: boolean
  }>(),
  { variant: 'ghost', size: 'md', type: 'button', tooltip: true },
)
</script>

<template>
  <UiTooltip :content="tooltip ? label : ''">
    <button
      :type="type"
      class="ui-icon-button"
      :data-variant="variant"
      :data-size="size"
      :aria-label="label"
      v-bind="$attrs"
    >
      <AppIcon :name="icon" :size="size === 'sm' ? 16 : 18" />
    </button>
  </UiTooltip>
</template>

<style scoped>
.ui-icon-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  width: var(--control-h);
  height: var(--control-h);
  padding: 0;
  border: 1px solid transparent;
  border-radius: var(--radius);
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  transition:
    background-color var(--dur) var(--ease),
    color var(--dur) var(--ease);
}

.ui-icon-button[data-size='sm'] {
  width: var(--control-h-sm);
  height: var(--control-h-sm);
}

.ui-icon-button:hover:not(:disabled),
.ui-icon-button[data-state='open'] {
  background: var(--surface-muted);
  color: var(--text);
}

.ui-icon-button[data-variant='secondary'] {
  border-color: var(--border);
  background: var(--surface);
}

.ui-icon-button[data-variant='danger']:hover:not(:disabled) {
  background: var(--danger-soft);
  color: var(--danger);
}

.ui-icon-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
