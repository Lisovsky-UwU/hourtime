<script setup lang="ts">
import { ref, watch } from 'vue'

import { usePreferencesStore } from '@/stores/preferences'
import type { TimeOfDay } from '@/utils/timeOfDay'
import { formatTimeOfDay, parseTimeOfDay } from '@/utils/timeOfDay'

/**
 * A time you type rather than pick.
 *
 * Commits on blur or Enter; anything unparseable snaps back to the last good
 * value instead of leaving the field in a state that cannot be saved.
 */
const model = defineModel<TimeOfDay>({ required: true })
// `aria-label`, `disabled` and friends are left to fall through to the input,
// this component's only root element — declaring them as props would shadow
// the real HTML attributes.
const emit = defineEmits<{ commit: [TimeOfDay] }>()

const preferences = usePreferencesStore()
const text = ref('')
const invalid = ref(false)

function show() {
  text.value = formatTimeOfDay(model.value, preferences.hourCycle)
  invalid.value = false
}

watch([model, () => preferences.hourCycle], show, {
  immediate: true,
  deep: true,
})

/**
 * The field shows minutes but the value may carry seconds. Typing the same
 * minute again (or nothing at all) must not quietly drop those seconds.
 */
function sameAsShown(parsed: TimeOfDay): boolean {
  const current = model.value
  return (
    parsed.hours === current.hours &&
    parsed.minutes === current.minutes &&
    parsed.dayOffset === current.dayOffset &&
    (parsed.seconds === 0 || parsed.seconds === current.seconds)
  )
}

function commit() {
  const parsed = parseTimeOfDay(text.value)
  if (!parsed) {
    invalid.value = true
    show()
    return
  }
  invalid.value = false
  if (sameAsShown(parsed)) {
    // Re-render anyway: "930" should settle into "09:30".
    show()
    return
  }
  model.value = parsed
  emit('commit', parsed)
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter') {
    event.preventDefault()
    ;(event.target as HTMLInputElement).blur()
  }
  if (event.key === 'Escape') {
    show()
    ;(event.target as HTMLInputElement).blur()
  }
}
</script>

<template>
  <input
    v-model="text"
    type="text"
    inputmode="numeric"
    autocomplete="off"
    class="time num"
    :class="{ invalid }"
    :style="{ width: `calc(${Math.max(5, text.length)}ch + 14px)` }"
    @blur="commit"
    @keydown="onKeydown"
  />
</template>

<style scoped>
.time {
  height: var(--control-h-sm);
  padding: 0 6px;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  background: transparent;
  color: inherit;
  /* `font` resets the numeric settings of .num, so they are repeated here. */
  font: inherit;
  font-variant-numeric: tabular-nums;
  font-variation-settings: 'SHRP' 100;
  text-align: center;
  transition:
    background-color var(--dur) var(--ease),
    border-color var(--dur) var(--ease);
}

.time:hover:not(:disabled) {
  border-color: var(--border);
}

.time:focus {
  border-color: var(--border-strong);
  background: var(--surface);
}

.time:focus-visible {
  outline: 2px solid var(--focus);
  outline-offset: -1px;
}

.time.invalid {
  border-color: var(--danger);
  color: var(--danger);
}

.time:disabled {
  color: var(--text-muted);
}

@media (width < 768px) {
  .time {
    font-size: max(1em, var(--text-md));
  }
}
</style>
