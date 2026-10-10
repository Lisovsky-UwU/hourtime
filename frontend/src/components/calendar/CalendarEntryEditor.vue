<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import type { EntryPatch } from '@/api/timeEntries'
import AutoTextarea from '@/components/AutoTextarea.vue'
import BillableToggle from '@/components/BillableToggle.vue'
import ProjectPicker from '@/components/ProjectPicker.vue'
import TagPicker from '@/components/TagPicker.vue'
import TimeField from '@/components/TimeField.vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiDatePicker from '@/components/ui/UiDatePicker.vue'
import { messageFor } from '@/composables/useApiError'
import { useDuration } from '@/composables/useDuration'
import { useTimerStore } from '@/stores/timer'
import type { TimeEntry } from '@/types'
import type { TimeOfDay } from '@/utils/timeOfDay'
import { combine, combineEnd, toDateInput, toTimeOfDay } from '@/utils/timeOfDay'

/**
 * The calendar's edit popover: the fields of `EntryRow`, stacked. Same rules -
 * every field saves itself, a value the server rejects snaps back.
 *
 * Saving goes through `save` from the calendar, a plain function rather than an
 * event: the comment is also saved when the popover closes, and by then an
 * unmounted component can no longer emit.
 */
const props = defineProps<{
  entry: TimeEntry
  save: (patch: EntryPatch) => Promise<TimeEntry>
}>()
const emit = defineEmits<{ remove: [TimeEntry]; continue: [TimeEntry] }>()

const { t } = useI18n()
const timer = useTimerStore()
const showDuration = useDuration()

const description = ref('')
const projectId = ref<string | null>(null)
const tagIds = ref<string[]>([])
const billable = ref(false)
const startDate = ref('')
const startTime = ref<TimeOfDay>({ hours: 0, minutes: 0, seconds: 0, dayOffset: 0 })
const endTime = ref<TimeOfDay | null>(null)
const error = ref<string | null>(null)

const isRunning = computed(() => props.entry.stopped_at === null)
const duration = computed(() => showDuration(timer.secondsOf(props.entry)))

function adopt(entry: TimeEntry) {
  description.value = entry.description
  projectId.value = entry.project_id
  tagIds.value = [...entry.tag_ids]
  billable.value = entry.billable
  startDate.value = toDateInput(entry.started_at)
  startTime.value = toTimeOfDay(entry.started_at)
  endTime.value = entry.stopped_at ? toTimeOfDay(entry.stopped_at, entry.started_at) : null
}

watch(() => props.entry, adopt, { immediate: true })

async function commit(patch: EntryPatch) {
  error.value = null
  try {
    await props.save(patch)
  } catch (cause) {
    error.value = messageFor(cause)
    adopt(props.entry)
  }
}

function commitDescription() {
  if (description.value === props.entry.description) return
  void commit({ description: description.value })
}

// Closing the popover by a click elsewhere does not always blur the field first.
onBeforeUnmount(commitDescription)

// Whole seconds, as in EntryRow: re-sending an unchanged time would truncate
// the microseconds the server keeps.
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

watch(tagIds, (value) => {
  const saved = props.entry.tag_ids
  if (value.length === saved.length && value.every((id) => saved.includes(id))) return
  void commit({ tag_ids: value })
})

watch(billable, (value) => {
  if (value === props.entry.billable) return
  void commit({ billable: value })
})
</script>

<template>
  <div class="cal-editor">
    <AutoTextarea
      v-model="description"
      class="description"
      :placeholder="t('entries.edit.descriptionPlaceholder')"
      :aria-label="t('entries.edit.description')"
      @blur="commitDescription"
    />

    <div class="line">
      <span class="project"><ProjectPicker v-model="projectId" /></span>
      <TagPicker v-model="tagIds" />
      <BillableToggle v-model="billable" />
    </div>

    <div class="line when">
      <UiDatePicker
        v-model="startDate"
        class="date"
        :label="t('entries.edit.date')"
        @change="commitTimes"
      />
      <span class="times">
        <TimeField
          v-model="startTime"
          :aria-label="t('entries.edit.startedAt')"
          @commit="commitTimes"
        />
        <span class="dash" aria-hidden="true">-</span>
        <TimeField
          v-if="endTime"
          v-model="endTime"
          :aria-label="t('entries.edit.stoppedAt')"
          @commit="commitTimes"
        />
        <span v-else class="running-label">{{ t('entries.running') }}</span>
      </span>
      <span class="duration num">
        <span v-if="isRunning" class="live-dot" aria-hidden="true" />
        {{ duration }}
      </span>
    </div>

    <p v-if="error" class="error" role="alert">{{ error }}</p>

    <div class="actions">
      <UiButton
        v-if="!isRunning"
        size="sm"
        icon="play"
        @click="emit('continue', props.entry)"
      >
        {{ t('entries.continue') }}
      </UiButton>
      <UiButton size="sm" variant="danger" icon="trash" @click="emit('remove', props.entry)">
        {{ t('common.delete') }}
      </UiButton>
    </div>
  </div>
</template>

<style scoped>
.cal-editor {
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: min(340px, calc(100vw - 40px));
}

/* Outlined from the start: unlike a row, the popover is plainly a form. */
.description {
  border-color: var(--border);
  font-size: var(--text-md);
}

.line {
  display: flex;
  align-items: center;
  gap: 8px;
}

.project {
  display: flex;
  flex: 1 1 auto;
  min-width: 0;
}

.when {
  flex-wrap: wrap;
  padding-top: 10px;
  border-top: 1px solid var(--border);
}

.times {
  display: flex;
  align-items: center;
  white-space: nowrap;
}

.dash {
  color: var(--text-muted);
}

.running-label {
  padding: 0 6px;
  color: var(--live);
  font-size: var(--text-xs);
  font-weight: 500;
}

.duration {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
  font-weight: 600;
}

.live-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--live);
  animation: live-pulse 2s ease-in-out infinite;
}

.error {
  color: var(--danger);
  font-size: var(--text-xs);
}

.actions {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

/* Delete stays at the far end even when Continue is not offered. */
.actions > :last-child {
  margin-left: auto;
}
</style>
