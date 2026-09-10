<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import type { EntryPatch } from '@/api/timeEntries'
import AppIcon from '@/components/AppIcon.vue'
import AutoTextarea from '@/components/AutoTextarea.vue'
import ProjectPicker from '@/components/ProjectPicker.vue'
import TimeField from '@/components/TimeField.vue'
import { messageFor } from '@/composables/useApiError'
import { useEntriesStore } from '@/stores/entries'
import { useTimerStore } from '@/stores/timer'
import type { TimeEntry } from '@/types'
import { formatCompact } from '@/utils/duration'
import type { TimeOfDay } from '@/utils/timeOfDay'
import { combine, combineEnd, toDateInput, toTimeOfDay } from '@/utils/timeOfDay'

/**
 * A time entry, editable where it sits.
 *
 * Every field commits itself — the comment on blur, the project on change, the
 * times on blur or Enter — so there is no Save button to forget to press. A
 * value the server rejects snaps back to what the server holds.
 */
const props = defineProps<{ entry: TimeEntry }>()
const emit = defineEmits<{ remove: [TimeEntry] }>()

const { t } = useI18n()
const entries = useEntriesStore()
const timer = useTimerStore()

const description = ref('')
const projectId = ref<string | null>(null)
const startDate = ref('')
const startTime = ref<TimeOfDay>({ hours: 0, minutes: 0, seconds: 0, dayOffset: 0 })
const endTime = ref<TimeOfDay | null>(null)
const error = ref<string | null>(null)

const isRunning = computed(() => props.entry.stopped_at === null)
const duration = computed(() => formatCompact(timer.secondsOf(props.entry)))

// Both ends of an entry show seconds as soon as either one has them.
const showSeconds = computed(
  () => startTime.value.seconds !== 0 || (endTime.value?.seconds ?? 0) !== 0,
)

function adopt(entry: TimeEntry) {
  description.value = entry.description
  projectId.value = entry.project_id
  startDate.value = toDateInput(entry.started_at)
  startTime.value = toTimeOfDay(entry.started_at)
  endTime.value = entry.stopped_at ? toTimeOfDay(entry.stopped_at, entry.started_at) : null
  error.value = null
}

// The store replaces the entry object after every save, and another device can
// change it under us — either way the fields follow the server.
watch(() => props.entry, adopt, { immediate: true })

async function commit(patch: EntryPatch) {
  error.value = null
  try {
    const updated = await entries.update(props.entry.id, patch)
    timer.applySaved(updated)
  } catch (cause) {
    error.value = messageFor(cause)
    adopt(props.entry)
  }
}

function commitDescription() {
  if (description.value === props.entry.description) return
  void commit({ description: description.value })
}

// Comparing whole seconds: the server stores microseconds, the row only ever
// shows seconds, and re-sending an unchanged time would silently truncate it.
function sameSecond(a: string, b: string): boolean {
  return Math.floor(Date.parse(a) / 1000) === Math.floor(Date.parse(b) / 1000)
}

function commitTimes() {
  const startedAt = combine(startDate.value, startTime.value)
  if (!startedAt) {
    adopt(props.entry)
    return
  }

  const patch: EntryPatch = {}
  if (!sameSecond(startedAt, props.entry.started_at)) patch.started_at = startedAt

  if (endTime.value) {
    const stoppedAt = combineEnd(startDate.value, startTime.value, endTime.value)
    if (!stoppedAt) {
      adopt(props.entry)
      return
    }
    if (!props.entry.stopped_at || !sameSecond(stoppedAt, props.entry.stopped_at)) {
      patch.stopped_at = stoppedAt
    }
  }

  if (Object.keys(patch).length === 0) return
  void commit(patch)
}

watch(projectId, (value) => {
  if (value === props.entry.project_id) return
  void commit({ project_id: value })
})

// Deleting is the one thing here that cannot be undone, so the icon asks once
// rather than opening a dialog.
const confirmingDelete = ref(false)
let confirmReset: number | null = null

function clearConfirm() {
  if (confirmReset !== null) window.clearTimeout(confirmReset)
  confirmReset = null
  confirmingDelete.value = false
}

function onDelete() {
  if (confirmingDelete.value) {
    clearConfirm()
    emit('remove', props.entry)
    return
  }
  confirmingDelete.value = true
  confirmReset = window.setTimeout(clearConfirm, 5000)
}

onUnmounted(clearConfirm)
</script>

<template>
  <li class="entry" :class="{ running: isRunning }">
    <AutoTextarea
      v-model="description"
      class="description"
      :placeholder="t('entries.edit.descriptionPlaceholder')"
      :aria-label="t('entries.edit.description')"
      @blur="commitDescription"
    />

    <ProjectPicker v-model="projectId" :aria-label="t('entries.edit.project')" class="project" />

    <input
      v-model="startDate"
      type="date"
      class="date"
      :aria-label="t('entries.edit.date')"
      @change="commitTimes"
    />

    <span class="times">
      <TimeField
        v-model="startTime"
        :show-seconds="showSeconds"
        :aria-label="t('entries.edit.startedAt')"
        @commit="commitTimes"
      />
      <span class="dash">–</span>
      <TimeField
        v-if="endTime"
        v-model="endTime"
        :show-seconds="showSeconds"
        :aria-label="t('entries.edit.stoppedAt')"
        @commit="commitTimes"
      />
      <span v-else class="muted small">{{ t('entries.running') }}</span>
    </span>

    <span class="duration mono">{{ duration }}</span>

    <button
      type="button"
      class="btn-ghost delete"
      :class="{ confirming: confirmingDelete }"
      :title="confirmingDelete ? t('entries.deleteConfirm') : t('common.delete')"
      :aria-label="confirmingDelete ? t('entries.deleteConfirm') : t('common.delete')"
      @click="onDelete"
      @blur="clearConfirm"
    >
      <AppIcon :name="confirmingDelete ? 'check' : 'trash'" />
    </button>

    <p v-if="error" class="banner row-error">{{ error }}</p>
  </li>
</template>

<style scoped>
.entry {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 8px 12px;
  border-top: 1px solid var(--border);
  flex-wrap: wrap;
}

.entry:first-child {
  border-top: none;
}

.entry.running {
  background: color-mix(in srgb, var(--accent) 6%, transparent);
}

.description {
  flex: 1 1 220px;
  min-width: 0;
  border-color: transparent;
  background: transparent;
  padding: 5px 8px;
}

.description:hover,
.description:focus {
  border-color: var(--border);
  background: var(--surface);
}

.project {
  flex: 0 0 auto;
}

.project :deep(select) {
  min-width: 130px;
  border-color: transparent;
  background: transparent;
  padding: 5px 6px;
}

.project :deep(select:hover),
.project :deep(select:focus) {
  border-color: var(--border);
  background: var(--surface);
}

.date {
  width: auto;
  padding: 4px 6px;
  border-color: transparent;
  background: transparent;
  color: var(--text-muted);
}

.date:hover,
.date:focus {
  border-color: var(--border);
  background: var(--surface);
  color: var(--text);
}

.times {
  display: flex;
  align-items: center;
  gap: 2px;
  white-space: nowrap;
}

.dash {
  color: var(--text-muted);
}

.duration {
  min-width: 64px;
  text-align: right;
  font-weight: 600;
  padding-top: 5px;
}

.delete {
  display: inline-flex;
  align-items: center;
  padding: 6px;
}

.delete:hover {
  color: var(--danger);
}

.delete.confirming {
  color: var(--danger);
  background: color-mix(in srgb, var(--danger) 14%, transparent);
}

.row-error {
  flex-basis: 100%;
  margin: 4px 0 0;
}

@media (width <= 720px) {
  .description {
    flex-basis: 100%;
  }
}
</style>
