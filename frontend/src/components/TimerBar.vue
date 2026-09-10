<script setup lang="ts">
import { onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import AppIcon from '@/components/AppIcon.vue'
import AutoTextarea from '@/components/AutoTextarea.vue'
import ProjectPicker from '@/components/ProjectPicker.vue'
import TimeField from '@/components/TimeField.vue'
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
  <section class="card timer">
    <div class="timer-main">
      <AutoTextarea
        v-model="description"
        class="description"
        :placeholder="t('timer.descriptionPlaceholder')"
        :aria-label="t('timer.descriptionPlaceholder')"
        @blur="commitDescription"
      />

      <ProjectPicker v-model="projectId" :aria-label="t('timer.selectProject')" />

      <span class="start">
        <span class="muted small">{{ t('timer.startTime') }}</span>
        <TimeField
          v-model="startTime"
          :aria-label="t('timer.startTime')"
          @commit="commitStart"
        />
      </span>

      <span class="elapsed mono" :class="{ live: timer.isRunning }">
        {{ formatClock(timer.elapsed) }}
      </span>

      <button
        type="button"
        class="action"
        :class="timer.isRunning ? 'stopping' : 'starting'"
        :disabled="busy"
        :title="timer.isRunning ? t('timer.stop') : t('timer.start')"
        :aria-label="timer.isRunning ? t('timer.stop') : t('timer.start')"
        @click="toggle"
      >
        <AppIcon :name="timer.isRunning ? 'stop' : 'play'" :size="20" />
      </button>
    </div>

    <p v-if="error" class="banner">{{ error }}</p>
  </section>
</template>

<style scoped>
.timer {
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.timer-main {
  display: flex;
  align-items: center;
  gap: 12px;
}

.description {
  flex: 1 1 auto;
  min-width: 0;
  border-color: transparent;
  background: transparent;
  font-size: 1rem;
  padding: 6px 8px;
}

.description:hover,
.description:focus {
  border-color: var(--border);
  background: var(--surface);
}

.start {
  display: flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
}

.elapsed {
  font-size: 1.35rem;
  font-weight: 600;
  letter-spacing: -0.02em;
  color: var(--text-muted);
  min-width: 8ch;
  text-align: right;
}

.elapsed.live {
  color: var(--text);
}

.action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border-radius: 50%;
  flex: 0 0 auto;
}

.action.starting {
  background: var(--accent);
  border-color: var(--accent);
  color: var(--accent-contrast);
}

.action.stopping {
  background: var(--danger);
  border-color: var(--danger);
  color: #fff;
}

.action:hover:not(:disabled) {
  filter: brightness(1.08);
}

@media (width <= 720px) {
  .timer-main {
    flex-wrap: wrap;
  }

  .description {
    flex-basis: 100%;
  }
}
</style>
