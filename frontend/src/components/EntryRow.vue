<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import type { EntryPatch } from '@/api/timeEntries'
import AutoTextarea from '@/components/AutoTextarea.vue'
import ProjectPicker from '@/components/ProjectPicker.vue'
import TimeField from '@/components/TimeField.vue'
import type { MenuEntry } from '@/components/ui/UiDropdownMenu.vue'
import UiDropdownMenu from '@/components/ui/UiDropdownMenu.vue'
import { messageFor } from '@/composables/useApiError'
import { useEntriesStore } from '@/stores/entries'
import { useTimerStore } from '@/stores/timer'
import type { TimeEntry } from '@/types'
import { formatClock } from '@/utils/duration'
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
/** Asks the list to delete; the list confirms first. */
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
const duration = computed(() => formatClock(timer.secondsOf(props.entry)))

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

const dateInput = ref<HTMLInputElement | null>(null)

/**
 * On phones the date field is hidden for room; the menu opens its picker.
 * Waits for the menu to close first: closing hands focus back to the menu
 * button, which would shut a picker opened any earlier.
 */
function pickDate() {
  window.setTimeout(() => {
    const input = dateInput.value
    if (!input) return
    input.focus()
    try {
      input.showPicker()
    } catch {
      // No picker API or no user activation left: the focused field still works.
    }
  }, 150)
}

const menu = computed<MenuEntry[]>(() => [
  { label: t('entries.changeDate'), icon: 'calendar', select: pickDate },
  'separator',
  {
    label: t('common.delete'),
    icon: 'trash',
    variant: 'danger',
    select: () => emit('remove', props.entry),
  },
])
</script>

<template>
  <li class="entry" :data-running="isRunning ? '' : undefined">
    <AutoTextarea
      v-model="description"
      class="description"
      :placeholder="t('entries.edit.descriptionPlaceholder')"
      :aria-label="t('entries.edit.description')"
      @blur="commitDescription"
    />

    <span class="project"><ProjectPicker v-model="projectId" compact /></span>

    <span class="when">
      <input
        ref="dateInput"
        v-model="startDate"
        type="date"
        class="date num"
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
        <span class="dash" aria-hidden="true">-</span>
        <TimeField
          v-if="endTime"
          v-model="endTime"
          :show-seconds="showSeconds"
          :aria-label="t('entries.edit.stoppedAt')"
          @commit="commitTimes"
        />
        <span v-else class="running-label">{{ t('entries.running') }}</span>
      </span>
    </span>

    <span class="duration num">
      <span v-if="isRunning" class="live-dot" aria-hidden="true" />
      {{ duration }}
    </span>

    <span class="menu">
      <UiDropdownMenu
        :items="menu"
        :label="t('entries.actionsFor', { name: description || t('timer.noDescription') })"
      />
    </span>

    <p v-if="error" class="row-error" role="alert">{{ error }}</p>
  </li>
</template>

<style scoped>
.entry {
  position: relative;
  display: grid;
  /* Fixed side columns, so projects and times line up from row to row. */
  grid-template-columns: minmax(0, 1fr) 200px 260px 80px 36px;
  grid-template-areas: 'description project when duration menu';
  align-items: center;
  column-gap: 8px;
  padding: 6px 8px 6px 8px;
  border-top: 1px solid var(--border);
}

.entry:first-child {
  border-top: none;
}

.description {
  grid-area: description;
}

.project {
  grid-area: project;
  display: flex;
  min-width: 0;
}

.when {
  grid-area: when;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 4px;
}

.times {
  display: flex;
  align-items: center;
  white-space: nowrap;
  color: var(--text-muted);
}

.times:focus-within,
.entry:hover .times {
  color: var(--text);
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

/* The day heading already says the date; the field only matters when moving
   an entry to another day, so it shows up on hover or focus. */
.date {
  height: var(--control-h-sm);
  padding: 0 4px;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-muted);
  font: inherit;
  font-size: var(--text-xs);
  font-variant-numeric: tabular-nums;
  font-variation-settings: 'SHRP' 100;
  opacity: 0;
  transition: opacity var(--dur) var(--ease);
}

.entry:hover .date,
.date:focus {
  opacity: 1;
}

@media (width < 900px) {
  /* Brought back on screen while in use from the menu. */
  .entry .date:focus {
    position: static;
    width: auto;
    height: var(--control-h-sm);
    clip-path: none;
  }
}

.date:hover {
  border-color: var(--border);
}

.date:focus-visible {
  outline: 2px solid var(--focus);
  outline-offset: -1px;
}

.duration {
  grid-area: duration;
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
  font-weight: 600;
}

.live-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--live);
  animation: live-pulse 2s ease-in-out infinite;
}

/* Hidden until the row is in use, but still reachable from the keyboard. */
.menu {
  grid-area: menu;
  opacity: 0;
  transition: opacity var(--dur) var(--ease);
}

.entry:hover .menu,
.entry:focus-within .menu,
.menu:has([data-state='open']) {
  opacity: 1;
}

.row-error {
  grid-column: 1 / -1;
  padding: 2px 8px 4px;
  color: var(--danger);
  font-size: var(--text-xs);
}

@media (hover: none) {
  .date,
  .menu {
    opacity: 1;
  }
}

/* Two lines on narrow screens: description, duration and menu on top; the
   project and the times below. Flex rather than grid, so the widths of one
   line do not dictate the columns of the other. */
@media (width < 900px) {
  .entry {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 2px 6px;
    padding: 8px 6px;
  }

  .description {
    order: 1;
    flex: 1 1 calc(100% - 128px);
    min-width: 0;
  }

  .duration {
    order: 2;
    flex: 0 0 76px;
  }

  .menu {
    order: 3;
    flex: 0 0 36px;
  }

  .project {
    order: 4;
    flex: 1 1 0;
  }

  .when {
    order: 5;
    flex: 0 0 auto;
  }

  .row-error {
    order: 6;
    flex-basis: 100%;
  }

  .date {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    overflow: hidden;
    clip-path: inset(50%);
  }
}
</style>
