<script setup lang="ts">
import { onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import AppIcon from '@/components/AppIcon.vue'
import AutoTextarea from '@/components/AutoTextarea.vue'
import ProjectPicker from '@/components/ProjectPicker.vue'
import TimeField from '@/components/TimeField.vue'
import { toast } from '@/components/ui/toast'
import { useAsyncAction } from '@/composables/useApiError'
import { useEntriesStore } from '@/stores/entries'
import { useTimerStore } from '@/stores/timer'
import { formatClock } from '@/utils/duration'
import { serverNow, serverNowIso } from '@/utils/serverTime'
import type { TimeOfDay } from '@/utils/timeOfDay'
import { combine, toDateInput, toTimeOfDay } from '@/utils/timeOfDay'

const { t } = useI18n()
const timer = useTimerStore()
// Every timer write returns the saved entry, so the list is folded in directly
// rather than refetched.
const entries = useEntriesStore()
const { busy, error, run } = useAsyncAction()

// The bar is sticky and sits on top of the list; a banner inside it would push
// the list around, so failures go to a toast.
watch(error, (message) => {
  if (message) toast.error(message)
})

const description = ref('')
const projectId = ref<string | null>(null)
const startTime = ref<TimeOfDay>(toTimeOfDay(serverNowIso()))
/** True once the user has typed a start time, which stops it tracking the clock. */
const startPinned = ref(false)

// While idle and untouched the field follows the clock, so hitting play always
// means "now" no matter how long the page has been open.
const clock = window.setInterval(() => {
  if (!timer.isRunning && !startPinned.value) startTime.value = toTimeOfDay(serverNowIso())
}, 1000)
onUnmounted(() => window.clearInterval(clock))

// The server owns the running entry: whenever it is replaced — start, stop, or
// a resync from another device — mirror it into the fields.
watch(
  () => timer.entry,
  (entry) => {
    description.value = entry?.description ?? ''
    projectId.value = entry?.project_id ?? null
    startTime.value = toTimeOfDay(entry?.started_at ?? serverNowIso())
    startPinned.value = false
  },
  { immediate: true },
)

/** The instant a fresh timer should start from, given only a time of day. */
function resolveStart(): string | null {
  const iso = combine(toDateInput(serverNowIso()), startTime.value)
  if (!iso) return null
  // A time later than now means yesterday — you cannot start in the future.
  const at = Date.parse(iso)
  return at > serverNow() ? new Date(at - 24 * 60 * 60 * 1000).toISOString() : iso
}

async function toggle() {
  if (timer.isRunning) {
    await run(async () => {
      const stopped = await timer.stop()
      if (stopped) entries.upsert(stopped)
    })
    return
  }

  const startedAt = resolveStart()
  await run(async () => {
    const started = await timer.start({
      description: description.value,
      project_id: projectId.value,
      ...(startedAt ? { started_at: startedAt } : {}),
    })
    entries.upsert(started)
  })
}

async function amend(patch: Parameters<typeof timer.amend>[0]) {
  await run(async () => {
    const updated = await timer.amend(patch)
    if (updated) entries.upsert(updated)
  })
}

function commitDescription() {
  if (!timer.entry || timer.entry.description === description.value) return
  void amend({ description: description.value })
}

watch(projectId, (value) => {
  if (!timer.entry || timer.entry.project_id === value) return
  void amend({ project_id: value })
})

function commitStart() {
  const running = timer.entry
  if (!running) {
    // Nothing to save yet; the value is simply where the next timer begins.
    startPinned.value = true
    return
  }
  const startedAt = combine(toDateInput(running.started_at), startTime.value)
  if (!startedAt || Date.parse(startedAt) === Date.parse(running.started_at)) return
  void amend({ started_at: startedAt })
}
</script>

<template>
  <section class="timer-bar" :data-running="timer.isRunning ? '' : undefined">
    <AutoTextarea
      v-model="description"
      class="description"
      :placeholder="t('timer.descriptionPlaceholder')"
      :aria-label="t('timer.descriptionPlaceholder')"
      @blur="commitDescription"
    />

    <div class="controls">
      <span class="project"><ProjectPicker v-model="projectId" /></span>

      <span class="start">
        <span class="start-label">{{ t('timer.startTime') }}</span>
        <TimeField v-model="startTime" :aria-label="t('timer.startTime')" @commit="commitStart" />
      </span>

      <span class="clock num" role="timer">
        {{ formatClock(timer.elapsed) }}
      </span>

      <button
        type="button"
        class="action"
        :disabled="busy"
        :aria-label="timer.isRunning ? t('timer.stop') : t('timer.start')"
        @click="toggle"
      >
        <AppIcon :name="timer.isRunning ? 'stop' : 'play'" :size="20" />
      </button>
    </div>
  </section>
</template>

<style scoped>
.timer-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 10px 10px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sheet);
  background: var(--surface);
  transition: border-color var(--dur) var(--ease);
}

.timer-bar[data-running] {
  border-color: color-mix(in srgb, var(--live) 45%, var(--border));
}

.description {
  /* Basis 0: the textarea is width 100%, and an auto basis would squeeze the
     controls instead of taking what is left after them. */
  flex: 1 1 0;
  min-width: 0;
  font-size: var(--text-md);
}

.controls {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 0 1 auto;
  min-width: 0;
}

/* Gives way first when space runs out; the name ends in an ellipsis. */
.project {
  display: flex;
  flex: 0 1 auto;
  min-width: 0;
  max-width: 220px;
}

.start {
  display: flex;
  align-items: center;
  gap: 2px;
  color: var(--text-muted);
  white-space: nowrap;
}

.start-label {
  font-size: var(--text-xs);
}

.clock {
  min-width: 5.2ch;
  padding: 0 6px;
  font-size: var(--text-clock);
  font-weight: 600;
  line-height: 1;
  letter-spacing: -0.02em;
  text-align: right;
  color: var(--text-muted);
  transition: color var(--dur) var(--ease);
}

.timer-bar[data-running] .clock {
  color: var(--text);
}

.action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  width: 52px;
  height: 52px;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: var(--accent);
  color: var(--accent-contrast);
  cursor: pointer;
  transition:
    background-color var(--dur) var(--ease),
    scale var(--dur) var(--ease);
}

.action:hover:not(:disabled) {
  background: var(--accent-hover);
}

.action:active:not(:disabled) {
  scale: 0.95;
}

.timer-bar[data-running] .action {
  background: var(--live);
  color: var(--live-contrast);
}

.timer-bar[data-running] .action:hover:not(:disabled) {
  background: color-mix(in srgb, var(--live) 88%, var(--text));
}

.action:disabled {
  opacity: 0.6;
  cursor: progress;
}

@media (width < 900px) {
  .timer-bar {
    flex-wrap: wrap;
    padding: 8px 8px 8px 10px;
  }

  .description {
    flex-basis: 100%;
  }

  .controls {
    flex: 1 1 100%;
  }

  .project {
    margin-right: auto;
  }

  .clock {
    font-size: var(--text-xl);
  }

  .action {
    width: 44px;
    height: 44px;
  }
}

@media (width < 480px) {
  .start-label {
    display: none;
  }

  .controls {
    gap: 4px;
  }

  .clock {
    min-width: 0;
    padding: 0 2px;
    font-size: 1.25rem;
  }

  /* An idle 0:00:00 says nothing; the room goes to the project name. */
  .timer-bar:not([data-running]) .clock {
    display: none;
  }
}
</style>
