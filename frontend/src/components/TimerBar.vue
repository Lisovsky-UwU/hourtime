<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import ProjectPicker from '@/components/ProjectPicker.vue'
import { useAsyncAction } from '@/composables/useApiError'
import { useTimerStore } from '@/stores/timer'
import { DATETIME_STEP, fromLocalInput, toLocalInput } from '@/utils/datetime'
import { formatClock } from '@/utils/duration'
import { serverNowIso } from '@/utils/serverTime'

const emit = defineEmits<{ changed: [] }>()

const { t, d } = useI18n()
const timer = useTimerStore()
const { busy, error, run } = useAsyncAction()

const description = ref('')
const projectId = ref<string | null>(null)
const startInput = ref('')
const editingStart = ref(false)

// The server is the source of truth: whenever the running entry is replaced
// (start, stop, or a resync from another device), mirror it into the form.
watch(
  () => timer.entry,
  (entry) => {
    description.value = entry?.description ?? ''
    projectId.value = entry?.project_id ?? null
    startInput.value = entry ? toLocalInput(entry.started_at) : ''
  },
  { immediate: true },
)

async function toggle() {
  if (timer.isRunning) {
    await run(async () => {
      await timer.stop()
      emit('changed')
    })
    return
  }

  const startedAt = startInput.value ? fromLocalInput(startInput.value) : null
  await run(async () => {
    await timer.start({
      description: description.value,
      project_id: projectId.value,
      ...(startedAt ? { started_at: startedAt } : {}),
    })
    editingStart.value = false
    emit('changed')
  })
}

async function commitDescription() {
  if (!timer.entry || timer.entry.description === description.value) return
  await run(async () => {
    await timer.amend({ description: description.value })
    emit('changed')
  })
}

watch(projectId, async (value) => {
  if (!timer.entry || timer.entry.project_id === value) return
  await run(async () => {
    await timer.amend({ project_id: value })
    emit('changed')
  })
})

async function applyStart() {
  const iso = fromLocalInput(startInput.value)
  if (!iso) return
  if (timer.entry) {
    await run(async () => {
      await timer.amend({ started_at: iso })
      emit('changed')
    })
  }
  editingStart.value = false
}

function openStartEditor() {
  // Default the picker to now so an unstarted timer has something sensible.
  if (!startInput.value) startInput.value = toLocalInput(serverNowIso())
  editingStart.value = true
}

function clearStartOverride() {
  startInput.value = ''
  editingStart.value = false
}
</script>

<template>
  <section class="card timer">
    <div class="timer-main">
      <input
        v-model="description"
        type="text"
        class="description"
        :placeholder="t('timer.descriptionPlaceholder')"
        :aria-label="t('timer.descriptionPlaceholder')"
        @blur="commitDescription"
        @keyup.enter="commitDescription"
      />

      <ProjectPicker v-model="projectId" :aria-label="t('timer.selectProject')" />

      <span class="elapsed mono" :class="{ live: timer.isRunning }">
        {{ formatClock(timer.elapsed) }}
      </span>

      <button
        type="button"
        class="btn-primary action"
        :class="{ stopping: timer.isRunning }"
        :disabled="busy"
        @click="toggle"
      >
        {{ timer.isRunning ? t('timer.stop') : t('timer.start') }}
      </button>
    </div>

    <div class="timer-meta small">
      <template v-if="editingStart">
        <label class="inline-label" for="start-at">{{ t('timer.startTime') }}</label>
        <input
          id="start-at"
          v-model="startInput"
          type="datetime-local"
          :step="DATETIME_STEP"
          class="start-input"
        />
        <button type="button" class="btn-link" :disabled="busy" @click="applyStart">
          {{ t('timer.apply') }}
        </button>
        <button type="button" class="btn-link muted" @click="clearStartOverride">
          {{ t('common.cancel') }}
        </button>
      </template>

      <template v-else-if="timer.entry">
        <span class="muted">
          {{ t('timer.startedAt', { time: d(new Date(timer.entry.started_at), 'time') }) }}
        </span>
        <button type="button" class="btn-link" @click="openStartEditor">
          {{ t('timer.adjustStart') }}
        </button>
      </template>

      <template v-else>
        <button type="button" class="btn-link" @click="openStartEditor">
          {{ t('timer.adjustStart') }}
        </button>
        <span v-if="startInput" class="badge">
          {{ d(new Date(startInput), 'time') }}
        </span>
      </template>
    </div>

    <p v-if="error" class="banner">{{ error }}</p>
  </section>
</template>

<style scoped>
.timer {
  padding: 14px 16px;
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
  padding-left: 0;
}

.description:hover {
  border-color: var(--border);
  padding-left: 11px;
}

.elapsed {
  font-size: 1.35rem;
  font-weight: 600;
  letter-spacing: -0.02em;
  color: var(--text-muted);
}

.elapsed.live {
  color: var(--text);
}

.action {
  min-width: 84px;
}

.action.stopping {
  background: var(--danger);
  border-color: var(--danger);
  color: #fff;
}

.timer-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  min-height: 24px;
}

.inline-label {
  margin: 0;
}

.start-input {
  width: auto;
  padding: 4px 8px;
  font-size: 0.85rem;
}

@media (width <= 640px) {
  .timer-main {
    flex-wrap: wrap;
  }

  .description {
    flex-basis: 100%;
  }
}
</style>
