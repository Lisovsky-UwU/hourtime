<script setup lang="ts">
import { useId } from 'vue'

/**
 * Label, control, hint. Renders a <label> around a single control so the two
 * are linked without ids; `group` is for several controls (a color palette)
 * that cannot share one label.
 */
withDefaults(defineProps<{ label: string; hint?: string; group?: boolean }>(), {
  hint: undefined,
  group: false,
})

const labelId = useId()
</script>

<template>
  <component
    :is="group ? 'div' : 'label'"
    class="ui-field"
    :role="group ? 'group' : undefined"
    :aria-labelledby="group ? labelId : undefined"
  >
    <span :id="labelId" class="ui-field-label">{{ label }}</span>
    <slot />
    <span v-if="hint" class="ui-field-hint">{{ hint }}</span>
  </component>
</template>

<style scoped>
.ui-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin: 0;
}

.ui-field-label {
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-weight: 500;
}

.ui-field-hint {
  color: var(--text-muted);
  font-size: var(--text-xs);
}
</style>
