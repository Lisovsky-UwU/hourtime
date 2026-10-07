<script setup lang="ts">
const model = defineModel<string>({ default: '' })

withDefaults(
  defineProps<{
    type?: 'text' | 'email' | 'password' | 'search'
    invalid?: boolean
  }>(),
  { type: 'text', invalid: false },
)
</script>

<template>
  <input
    v-model="model"
    :type="type"
    class="ui-input"
    :aria-invalid="invalid || undefined"
  />
</template>

<style scoped>
.ui-input {
  width: 100%;
  height: var(--control-h);
  padding: 0 10px;
  border: 1px solid var(--control-border);
  border-radius: var(--radius);
  background: var(--surface);
  color: var(--text);
  font: inherit;
  transition: border-color var(--dur) var(--ease);
}

.ui-input::placeholder {
  color: var(--text-muted);
  opacity: 1;
}

.ui-input:hover:not(:disabled) {
  border-color: var(--text-muted);
}

.ui-input:focus-visible {
  outline: 2px solid var(--focus);
  outline-offset: -1px;
  border-color: transparent;
}

.ui-input[aria-invalid='true'],
.ui-input[aria-invalid='true']:focus-visible {
  border-color: var(--danger);
  outline-color: var(--danger);
}

.ui-input:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

/* Below 16px iOS zooms into the field on focus. */
@media (width < 768px) {
  .ui-input {
    font-size: var(--text-md);
  }
}
</style>
