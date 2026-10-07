<script setup lang="ts">
import { useId } from 'vue'
import { SwitchRoot, SwitchThumb } from 'reka-ui'

const model = defineModel<boolean>({ default: false })

withDefaults(defineProps<{ label: string; hint?: string; disabled?: boolean }>(), {
  hint: undefined,
  disabled: false,
})

const id = useId()
</script>

<template>
  <div class="ui-switch-row">
    <span class="ui-switch-text">
      <label :for="id" class="ui-switch-label">{{ label }}</label>
      <span v-if="hint" class="ui-switch-hint">{{ hint }}</span>
    </span>
    <SwitchRoot :id="id" v-model="model" class="ui-switch" :disabled="disabled">
      <SwitchThumb class="ui-switch-thumb" />
    </SwitchRoot>
  </div>
</template>

<style scoped>
.ui-switch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.ui-switch-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.ui-switch-label {
  margin: 0;
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--text);
  cursor: pointer;
}

.ui-switch-hint {
  font-size: var(--text-xs);
  color: var(--text-muted);
}

.ui-switch {
  position: relative;
  flex: 0 0 auto;
  width: 36px;
  height: 20px;
  padding: 0;
  border: 0;
  border-radius: var(--radius-full);
  background: var(--control-border);
  cursor: pointer;
  transition: background-color var(--dur) var(--ease);
}

.ui-switch[data-state='checked'] {
  background: var(--accent);
}

.ui-switch:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.ui-switch-thumb {
  display: block;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: light-dark(#ffffff, var(--text));
  translate: 2px 0;
  transition: translate var(--dur) var(--ease);
}

.ui-switch-thumb[data-state='checked'] {
  background: var(--accent-contrast);
  translate: 18px 0;
}
</style>
