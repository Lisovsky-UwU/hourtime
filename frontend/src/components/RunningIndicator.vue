<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { useDuration } from '@/composables/useDuration'
import { useProjectsStore } from '@/stores/projects'
import { useTimerStore } from '@/stores/timer'

/** The running timer, visible from every screen; a link back to it. */
withDefaults(defineProps<{ compact?: boolean }>(), { compact: false })

const { t } = useI18n()
const timer = useTimerStore()
const showDuration = useDuration()
const projects = useProjectsStore()

const project = computed(() => projects.find(timer.entry?.project_id ?? null))
const title = computed(
  () => timer.entry?.description || project.value?.name || t('timer.noDescription'),
)
</script>

<template>
  <RouterLink
    v-if="timer.isRunning"
    :to="{ name: 'timer' }"
    class="running"
    :data-compact="compact ? '' : undefined"
    :aria-label="`${t('timer.running')}: ${title}`"
  >
    <span class="live-dot" aria-hidden="true" />
    <span class="num clock">{{ showDuration(timer.elapsed) }}</span>
    <span v-if="!compact" class="title">
      <span v-if="project" class="project-dot" :style="{ background: project.color }" />
      <span class="title-text">{{ title }}</span>
    </span>
  </RouterLink>
</template>

<style scoped>
.running {
  display: grid;
  grid-template-columns: auto 1fr;
  align-items: center;
  column-gap: 8px;
  row-gap: 2px;
  padding: 8px 10px;
  border-radius: var(--radius);
  color: var(--text);
  text-decoration: none;
}

.running:hover {
  background: var(--surface-muted);
  text-decoration: none;
}

.running[data-compact] {
  display: inline-flex;
  padding: 4px 8px;
}

.live-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--live);
  animation: live-pulse 2s ease-in-out infinite;
}

.clock {
  font-weight: 600;
}

.title {
  grid-column: 2;
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  color: var(--text-muted);
  font-size: var(--text-xs);
}

.title-text {
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.project-dot {
  flex: 0 0 auto;
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

</style>
