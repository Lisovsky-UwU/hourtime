<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { useDuration } from '@/composables/useDuration'
import { usePreferencesStore } from '@/stores/preferences'
import { useProjectsStore } from '@/stores/projects'
import { useTimerStore } from '@/stores/timer'
import type { TimeEntry } from '@/types'
import { formatTimeOfDay, toTimeOfDay } from '@/utils/timeOfDay'

/**
 * What a calendar block says about its entry. `start` and `end` come from the
 * calendar rather than the entry, so a block being dragged or resized shows
 * the times it would get on drop.
 */
const props = defineProps<{ entry: TimeEntry; start: Date; end: Date }>()

const { t } = useI18n()
const preferences = usePreferencesStore()
const projects = useProjectsStore()
const timer = useTimerStore()
const showDuration = useDuration()

const running = computed(() => props.entry.stopped_at === null)
const project = computed(() => projects.find(props.entry.project_id))
const minutes = computed(() => (props.end.getTime() - props.start.getTime()) / 60_000)

const times = computed(() => {
  const startIso = props.start.toISOString()
  const from = formatTimeOfDay(toTimeOfDay(startIso), preferences.hourCycle)
  if (running.value) return `${from} -`
  const to = formatTimeOfDay(toTimeOfDay(props.end.toISOString(), startIso), preferences.hourCycle)
  return `${from} - ${to}`
})

const duration = computed(() =>
  showDuration(
    running.value
      ? timer.secondsOf(props.entry)
      : Math.round((props.end.getTime() - props.start.getTime()) / 1000),
  ),
)
</script>

<template>
  <div
    class="cal-block"
    :data-entry-id="entry.id"
    :data-size="minutes < 40 ? 'short' : minutes < 75 ? 'medium' : undefined"
  >
    <span class="cal-block-description" :data-empty="entry.description ? undefined : ''">
      {{ entry.description || t('timer.noDescription') }}
    </span>
    <span v-if="project" class="cal-block-project">{{ project.name }}</span>
    <span class="cal-block-time num">
      <span v-if="running" class="live-dot" aria-hidden="true" />
      <span class="cal-block-range">{{ times }}</span>
      <span class="cal-block-duration">{{ duration }}</span>
    </span>
  </div>
</template>

<style scoped>
/* Tall blocks stack description, project and time; the calendar clips
   whatever does not fit, so the description is the line that always shows. */
.cal-block {
  display: flex;
  flex-direction: column;
  gap: 1px;
  height: 100%;
  min-width: 0;
  padding: 3px 6px;
  overflow: hidden;
  color: var(--text);
  font-size: var(--text-xs);
  line-height: 1.3;
}

.cal-block-description {
  font-size: var(--text-sm);
  font-weight: 500;
  overflow-wrap: anywhere;
}

.cal-block-description[data-empty] {
  color: var(--text-muted);
  font-weight: 400;
}

.cal-block-project {
  color: var(--text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cal-block-time {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text-muted);
  white-space: nowrap;
}

.cal-block-duration {
  margin-left: auto;
  color: var(--text);
  font-weight: 600;
}

/* Up to half an hour or so: one line, description and duration side by side. */
.cal-block[data-size='short'] {
  flex-direction: row;
  align-items: baseline;
  gap: 6px;
  padding-block: 1px;
}

.cal-block[data-size='short'] .cal-block-description {
  flex: 1 1 auto;
  min-width: 0;
  overflow: hidden;
  font-size: var(--text-xs);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cal-block[data-size='short'] :is(.cal-block-project, .cal-block-range) {
  display: none;
}

.cal-block[data-size='medium'] .cal-block-description {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.live-dot {
  flex: 0 0 auto;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--live);
  animation: live-pulse 2s ease-in-out infinite;
}
</style>
