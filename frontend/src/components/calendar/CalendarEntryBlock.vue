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
  <div class="cal-block" :data-entry-id="entry.id">
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
/* The layout follows the height the block really gets (the calendar makes
   .fc-event-main a size container), not the entry's length: a block cut at
   midnight is shorter than its entry. Tall blocks stack description, project
   and time; only the description gives way, and only by whole lines. */
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

.cal-block > * {
  flex-shrink: 0;
}

.cal-block-description {
  overflow: hidden;
  font-size: var(--text-sm);
  font-weight: 500;
  overflow-wrap: anywhere;
  /* 40px: padding plus the project and time rows below. */
  max-height: round(down, 100cqh - 40px, 1lh);
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

/* No room for a line of description over project and time: two rows,
   one line of description and the time. */
@container (height < 59px) {
  .cal-block-project {
    display: none;
  }

  .cal-block-description {
    max-height: none;
    font-size: var(--text-xs);
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

/* No room for two rows: one line, description and duration side by side. */
@container (height < 39px) {
  .cal-block {
    flex-direction: row;
    align-items: baseline;
    gap: 6px;
    padding-block: 1px;
  }

  .cal-block-description {
    flex: 1 1 auto;
    min-width: 0;
  }

  .cal-block-range {
    display: none;
  }
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
