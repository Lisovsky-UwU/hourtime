<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { useBilling } from '@/composables/useBilling'

/**
 * Billable mark of an entry: the workspace currency's own symbol, stamped in
 * ink when the time is billable and in pencil when it is not - the same
 * ink-or-pencil rule as the tag button next to it. `readonly` shows the mark
 * without the button, for summary lines.
 */
const model = defineModel<boolean>({ required: true })
withDefaults(defineProps<{ disabled?: boolean; readonly?: boolean }>(), {
  disabled: false,
  readonly: false,
})

const { t } = useI18n()
const { symbol } = useBilling()

const title = computed(() => (model.value ? t('billing.billable') : t('billing.notBillable')))
</script>

<template>
  <span
    v-if="readonly"
    class="billable-mark"
    :data-on="model ? '' : undefined"
    :title="title"
    :aria-label="title"
    role="img"
  >
    {{ symbol }}
  </span>
  <button
    v-else
    type="button"
    class="billable-mark billable-toggle"
    :data-on="model ? '' : undefined"
    :aria-pressed="model"
    :aria-label="t('billing.billable')"
    :title="title"
    :disabled="disabled"
    @click="model = !model"
  >
    {{ symbol }}
  </button>
</template>

<style scoped>
.billable-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: var(--control-h-sm);
  height: var(--control-h-sm);
  padding: 0 4px;
  color: var(--text-muted);
  font-size: var(--text-sm);
  font-weight: 400;
  line-height: 1;
  white-space: nowrap;
}

/* A symbol, not a word: printed like the digits next to it. */
.billable-mark[data-on] {
  color: var(--text);
  font-weight: 600;
  font-variation-settings: 'SHRP' 100;
}

.billable-toggle {
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  background: transparent;
  font-family: inherit;
  cursor: pointer;
  transition: background-color var(--dur) var(--ease);
}

.billable-toggle:hover:not(:disabled) {
  background: var(--surface-muted);
}

.billable-toggle:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
