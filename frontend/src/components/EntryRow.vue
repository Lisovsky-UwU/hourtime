<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { useProjectsStore } from '@/stores/projects'
import { useTimerStore } from '@/stores/timer'
import type { TimeEntry } from '@/types'
import { formatCompact } from '@/utils/duration'

const props = defineProps<{ entry: TimeEntry }>()
const emit = defineEmits<{ edit: [TimeEntry]; remove: [TimeEntry] }>()

const { t, d } = useI18n()
const projects = useProjectsStore()
const timer = useTimerStore()

const project = computed(() => projects.find(props.entry.project_id))

const duration = computed(() => formatCompact(timer.secondsOf(props.entry)))
</script>

<template>
  <li class="entry">
    <div class="details">
      <span class="description" :class="{ empty: !entry.description }">
        {{ entry.description || t('entries.noDescription') }}
      </span>

      <span v-if="project" class="badge">
        <span class="dot" :style="{ background: project.color }" />
        {{ project.name }}
      </span>
    </div>

    <span class="times muted small mono">
      {{ d(new Date(entry.started_at), 'time') }} –
      <template v-if="entry.stopped_at">{{ d(new Date(entry.stopped_at), 'time') }}</template>
      <template v-else>{{ t('entries.running') }}</template>
    </span>

    <span class="duration mono">{{ duration }}</span>

    <span class="actions">
      <button type="button" class="btn-ghost" @click="emit('edit', entry)">
        {{ t('common.edit') }}
      </button>
      <button type="button" class="btn-ghost danger" @click="emit('remove', entry)">
        {{ t('common.delete') }}
      </button>
    </span>
  </li>
</template>

<style scoped>
.entry {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  border-top: 1px solid var(--border);
}

.entry:first-child {
  border-top: none;
}

.details {
  flex: 1 1 auto;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.description {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.description.empty {
  color: var(--text-muted);
  font-style: italic;
}

.times {
  white-space: nowrap;
}

.duration {
  min-width: 62px;
  text-align: right;
  font-weight: 600;
}

.actions {
  display: flex;
  gap: 2px;
}

.actions .danger:hover {
  color: var(--danger);
}

@media (width <= 640px) {
  .entry {
    flex-wrap: wrap;
  }

  .details {
    flex-basis: 100%;
  }
}
</style>
