<script setup lang="ts">
import { ref, watch } from 'vue'

import { usePreferencesStore } from '@/stores/preferences'
import type { TimeOfDay } from '@/utils/timeOfDay'
import { formatTimeOfDay, parseTimeOfDay, sameTimeOfDay } from '@/utils/timeOfDay'

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
const props = withDefaults(defineProps<{ showSeconds?: boolean }>(), { showSeconds: false })
const emit = defineEmits<{ commit: [TimeOfDay] }>()

const preferences = usePreferencesStore()
const text = ref('')
const invalid = ref(false)

function show() {
  text.value = formatTimeOfDay(model.value, preferences.hourCycle, props.showSeconds)
  invalid.value = false
}

watch([model, () => preferences.hourCycle, () => props.showSeconds], show, {
  immediate: true,
  deep: true,
})

function commit() {
  const parsed = parseTimeOfDay(text.value)
  if (!parsed) {
    invalid.value = true
    show()
    return
  }
  invalid.value = false
  if (sameTimeOfDay(parsed, model.value)) {
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
    class="time mono"
    :class="{ invalid }"
    :style="{ width: `${Math.max(6, text.length + 1)}ch` }"
    @blur="commit"
    @keydown="onKeydown"
  />
</template>

<style scoped>
.time {
  padding: 4px 6px;
  text-align: center;
  border-color: transparent;
  background: transparent;
}

.time:hover:not(:disabled),
.time:focus {
  border-color: var(--border);
  background: var(--surface);
}

.time.invalid {
  border-color: var(--danger);
  color: var(--danger);
}

.time:disabled {
  opacity: 1;
  color: var(--text-muted);
}
</style>
