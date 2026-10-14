<script setup lang="ts">
import { ref, watch } from 'vue'

import { useDuration } from '@/composables/useDuration'
import { parseDuration } from '@/utils/timesheet'

/**
 * One day of one timesheet row: the total, typed over in place. The value is
 * saved on Enter or when focus leaves, and only if the text was changed, so
 * seconds hidden by the duration format are not rewritten by a pass with Tab.
 */
const props = defineProps<{
  seconds: number
  label: string
  /** A future day or a running entry: shown, not typed into. */
  readonly?: boolean
  running?: boolean
  /** Resolves false when nothing was saved and the old value should come back. */
  commit: (seconds: number) => Promise<boolean>
}>()

const duration = useDuration()
const shownText = () => (props.seconds > 0 ? duration(props.seconds) : '')

const text = ref(shownText())
const invalid = ref(false)
const saving = ref(false)
const focused = ref(false)

// Ticking and saved values land here, but never over what is being typed.
watch(shownText, (next) => {
  if (!focused.value && !saving.value) text.value = next
})

function revert() {
  text.value = shownText()
  invalid.value = false
}

async function save() {
  if (text.value.trim() === shownText()) return revert()
  const seconds = parseDuration(text.value)
  if (seconds === null) {
    invalid.value = true
    return
  }
  invalid.value = false
  saving.value = true
  try {
    if (!(await props.commit(seconds))) revert()
  } finally {
    saving.value = false
  }
  if (!focused.value) text.value = shownText()
}

function onFocus(event: FocusEvent) {
  focused.value = true
  ;(event.target as HTMLInputElement).select()
}

function onBlur() {
  focused.value = false
  void save()
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter') {
    event.preventDefault()
    ;(event.target as HTMLInputElement).blur()
  } else if (event.key === 'Escape') {
    revert()
    ;(event.target as HTMLInputElement).blur()
  }
}
</script>

<template>
  <span v-if="readonly" class="ts-cell num" :data-running="running ? '' : undefined">
    <span v-if="running" class="live-dot" aria-hidden="true" />
    {{ shownText() }}
  </span>
  <input
    v-else
    v-model="text"
    class="ts-cell ts-input num"
    inputmode="decimal"
    autocomplete="off"
    :aria-label="label"
    :aria-invalid="invalid || undefined"
    :disabled="saving"
    @focus="onFocus"
    @blur="onBlur"
    @keydown="onKeydown"
  />
</template>

<style scoped>
.ts-cell {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
  width: 100%;
  min-height: 34px;
  padding: 0 8px;
  color: var(--text);
  text-align: right;
}

/* A cell is a printed figure on the card until it is touched: no box at rest,
   a ruled one on hover, the field's own frame while typing. */
.ts-input {
  border: 1px solid transparent;
  border-radius: 8px;
  background: transparent;
  font: inherit;
  transition:
    border-color var(--dur) var(--ease),
    background-color var(--dur) var(--ease);
}

.ts-input:hover {
  border-color: var(--border);
}

.ts-input:focus {
  border-color: var(--control-border);
  background: var(--surface);
  outline: 2px solid var(--focus);
  outline-offset: -1px;
}

.ts-input[aria-invalid] {
  border-color: var(--danger);
  outline-color: var(--danger);
}

.ts-input:disabled {
  opacity: 0.55;
}

.live-dot {
  flex: 0 0 auto;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--live);
  animation: live-pulse 2s ease-in-out infinite;
}

@media (pointer: coarse) {
  .ts-cell {
    min-height: 44px;
  }
}
</style>
