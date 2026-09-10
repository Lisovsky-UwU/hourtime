<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { useProjectsStore } from '@/stores/projects'

const model = defineModel<string | null>({ required: true })
const props = withDefaults(defineProps<{ ariaLabel?: string }>(), { ariaLabel: '' })

const { t } = useI18n()
const projects = useProjectsStore()

/**
 * Archived projects stay selectable only while an entry already points at one,
 * so editing an old entry does not silently drop its project.
 */
const options = computed(() => {
  const visible = projects.items.filter((project) => !project.archived)
  const current = projects.find(model.value)
  return current && current.archived ? [current, ...visible] : visible
})

const selected = computed(() => projects.find(model.value))

function onChange(event: Event) {
  const value = (event.target as HTMLSelectElement).value
  model.value = value === '' ? null : value
}
</script>

<template>
  <div class="picker">
    <span class="dot" :style="{ background: selected?.color ?? 'transparent' }" />
    <select
      :value="model ?? ''"
      :aria-label="props.ariaLabel || t('timer.selectProject')"
      @change="onChange"
    >
      <option value="">{{ t('timer.noProject') }}</option>
      <option v-for="project in options" :key="project.id" :value="project.id">
        {{ project.name }}
      </option>
    </select>
  </div>
</template>

<style scoped>
.picker {
  display: flex;
  align-items: center;
  gap: 8px;
}

.picker select {
  /* Wide enough that real project names are readable, not just their first word. */
  min-width: 160px;
}

.dot {
  box-shadow: inset 0 0 0 1px rgb(0 0 0 / 15%);
}
</style>
