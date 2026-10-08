<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import AppIcon from '@/components/AppIcon.vue'
import BillableToggle from '@/components/BillableToggle.vue'
import EntryRow from '@/components/EntryRow.vue'
import UiIconButton from '@/components/ui/UiIconButton.vue'
import { useDuration } from '@/composables/useDuration'
import { usePreferencesStore } from '@/stores/preferences'
import { useProjectsStore } from '@/stores/projects'
import { useTagsStore } from '@/stores/tags'
import { useTimerStore } from '@/stores/timer'
import type { TimeEntry } from '@/types'
import { formatTimeOfDay, toTimeOfDay } from '@/utils/timeOfDay'

/**
 * Entries of one day with the same description, project, tags and billable
 * flag, folded into one line the way Toggl does it: the count opens the entries, each still
 * editable on its own. The header itself is read-only - which of the entries
 * a change to it should land on is not obvious.
 */
const props = defineProps<{
  /** Newest first, all finished: the running entry always stays a row of its own. */
  entries: TimeEntry[]
}>()
const emit = defineEmits<{ remove: [TimeEntry]; continue: [TimeEntry]; duplicate: [TimeEntry] }>()

const { t } = useI18n()
const timer = useTimerStore()
const showDuration = useDuration()
const projects = useProjectsStore()
const tags = useTagsStore()
const preferences = usePreferencesStore()

const expanded = ref(false)

const newest = computed(() => props.entries[0]!)
const oldest = computed(() => props.entries.at(-1)!)
const project = computed(() => projects.find(newest.value.project_id))
const tagNames = computed(() => tags.namesOf(newest.value.tag_ids))
const total = computed(() =>
  showDuration(props.entries.reduce((sum, entry) => sum + timer.secondsOf(entry), 0)),
)

/** From the first start to the last end; the gaps in between are not shown. */
const span = computed(() => {
  const from = oldest.value.started_at
  const to = newest.value.stopped_at ?? from
  const cycle = preferences.hourCycle
  return {
    from: formatTimeOfDay(toTimeOfDay(from), cycle),
    to: formatTimeOfDay(toTimeOfDay(to, from), cycle),
  }
})

/** The width TimeField gives itself, so the header's times sit over the rows' fields. */
function fieldWidth(text: string): string {
  return `calc(${Math.max(5, text.length)}ch + 14px)`
}

const name = computed(() => newest.value.description || t('timer.noDescription'))
</script>

<template>
  <li class="group" :data-expanded="expanded ? '' : undefined">
    <div class="head">
      <span class="description">
        <button
          type="button"
          class="count num"
          :aria-expanded="expanded"
          :aria-label="t('entries.group.toggle', { count: entries.length, name })"
          @click="expanded = !expanded"
        >
          {{ entries.length }}
        </button>
        <span class="text" :class="{ muted: !newest.description }">{{ name }}</span>
      </span>

      <span v-if="project" class="project" :title="project.name">
        <span class="ui-combobox-dot" :style="{ background: project.color }" />
        <span class="project-name">{{ project.name }}</span>
      </span>

      <span
        v-if="tagNames.length"
        class="tags"
        :title="tagNames.join(', ')"
        :aria-label="`${t('tags.label')}: ${tagNames.join(', ')}`"
      >
        <AppIcon name="tag" :size="16" />
        <span class="num">{{ tagNames.length }}</span>
      </span>

      <span v-if="newest.billable" class="billable">
        <BillableToggle :model-value="true" readonly />
      </span>

      <span class="times num">
        <span class="time" :style="{ width: fieldWidth(span.from) }">{{ span.from }}</span>
        <span aria-hidden="true">-</span>
        <span class="time" :style="{ width: fieldWidth(span.to) }">{{ span.to }}</span>
      </span>

      <span class="duration num">{{ total }}</span>

      <span class="continue">
        <UiIconButton
          icon="play"
          size="sm"
          :label="t('entries.continue')"
          @click="emit('continue', newest)"
        />
      </span>
    </div>

    <ul v-if="expanded" class="children" :aria-label="name">
      <EntryRow
        v-for="entry in entries"
        :key="entry.id"
        :entry="entry"
        @remove="emit('remove', $event)"
        @continue="emit('continue', $event)"
        @duplicate="emit('duplicate', $event)"
      />
    </ul>
  </li>
</template>

<style scoped>
.group {
  border-top: 1px solid var(--border);
}

.group:first-child {
  border-top: none;
}

/* The same columns as EntryRow, so the header lines up with the rows. */
.head {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 200px 44px 36px 116px 160px 64px 36px 36px;
  grid-template-areas: 'description project tags billable date times duration continue menu';
  align-items: center;
  column-gap: 8px;
  /* As tall as a row, whose menu button sets its height. */
  min-height: calc(var(--control-h) + 12px);
  padding: 6px 8px;
}

.group[data-expanded] > .head {
  border-bottom: 1px solid var(--border);
}

.description {
  grid-area: description;
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

/* The count is the toggle: a small stamped box, filled while open. */
.count {
  flex: 0 0 auto;
  min-width: 26px;
  height: 26px;
  padding: 0 6px;
  border: 1px solid var(--control-border);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-muted);
  font: inherit;
  font-size: var(--text-xs);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  font-variation-settings: 'SHRP' 100;
  cursor: pointer;
  transition:
    background-color var(--dur) var(--ease),
    border-color var(--dur) var(--ease),
    color var(--dur) var(--ease);
}

.count:hover {
  border-color: var(--text-muted);
  color: var(--text);
}

.count[aria-expanded='true'] {
  border-color: var(--accent);
  background: var(--accent-soft);
  color: var(--accent);
}

.count:focus-visible {
  outline: 2px solid var(--focus);
  outline-offset: 1px;
}

/* Same inset as the text in the row's comment box. */
.text {
  min-width: 0;
  padding: 0 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.project {
  grid-area: project;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  padding: 0 9px;
}

.project-name {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ui-combobox-dot {
  flex: 0 0 auto;
}

/* Read-only copy of the rows' tag button, at the same spot. */
.tags {
  grid-area: tags;
  justify-self: center;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--text-xs);
  font-weight: 500;
}

.billable {
  grid-area: billable;
  justify-self: center;
}

/* Laid out like the time fields of a row: same widths, same dash between. */
.times {
  grid-area: times;
  justify-self: end;
  display: flex;
  align-items: center;
  color: var(--text-muted);
  white-space: nowrap;
}

.time {
  text-align: center;
}

.duration {
  grid-area: duration;
  justify-self: end;
  font-weight: 600;
}

.continue {
  grid-area: continue;
  opacity: 0;
  transition: opacity var(--dur) var(--ease);
}

.head:hover .continue,
.head:focus-within .continue {
  opacity: 1;
}

.head .continue :deep(.ui-icon-button):hover {
  color: var(--accent);
}

/* Indented by the width of the count, so the comments line up under the header's. */
.children {
  list-style: none;
  margin: 0 0 0 32px;
  padding: 0;
}

@media (hover: none) {
  .continue {
    opacity: 1;
  }
}

@media (width < 900px) {
  .head {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 2px 6px;
    padding: 8px 6px;
  }

  .description {
    order: 1;
    /* Exactly what the duration, continue and menu leave (76 + 36 + 36 + 3 gaps),
       so the project starts the second line instead of squeezing into the first. */
    flex: 1 1 calc(100% - 166px);
  }

  .duration {
    order: 2;
    flex: 0 0 76px;
    text-align: right;
  }

  .continue {
    order: 3;
    flex: 0 0 36px;
  }

  /* Empty slot where a row has its menu, so the durations stay in one column. */
  .head::after {
    content: '';
    order: 3;
    flex: 0 0 36px;
  }

  .project {
    order: 4;
    flex: 1 1 0;
  }

  .tags {
    order: 4;
    padding: 0 6px;
  }

  .billable {
    order: 4;
  }

  .times {
    order: 5;
    margin-left: auto;
  }

  .children {
    margin-left: 16px;
  }
}

/* The rows' time fields grow to 16px here (no zoom on iOS); the header keeps up. */
@media (width < 768px) {
  .times {
    font-size: max(1em, var(--text-md));
  }
}
</style>
