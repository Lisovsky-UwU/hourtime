<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import type { ComboboxItem } from '@/components/ui/UiCombobox.vue'
import UiCombobox from '@/components/ui/UiCombobox.vue'
import { toast } from '@/components/ui/toast'
import { messageFor } from '@/composables/useApiError'
import { useProjectsStore } from '@/stores/projects'
import { nextProjectColor } from '@/utils/projectColors'

/**
 * Project choice with search, and creating a project without leaving the
 * timer: type a name that does not exist yet and pick "Create".
 */
const model = defineModel<string | null>({ required: true })
withDefaults(defineProps<{ compact?: boolean; disabled?: boolean }>(), {
  compact: false,
  disabled: false,
})

const { t } = useI18n()
const projects = useProjectsStore()

/**
 * Archived projects stay selectable only while an entry already points at one,
 * so editing an old entry does not silently drop its project.
 */
const items = computed<ComboboxItem[]>(() => {
  const visible = projects.active
  const current = projects.find(model.value)
  const list = current && current.archived ? [current, ...visible] : visible
  return [...list]
    .sort((a, b) => a.name.localeCompare(b.name))
    .map((project) => ({ value: project.id, label: project.name, color: project.color }))
})

async function create(name: string) {
  try {
    const color = nextProjectColor(projects.active.map((project) => project.color))
    const project = await projects.create(name, color)
    model.value = project.id
  } catch (cause) {
    // The picker is already closed; a toast is the only place left to say why.
    toast.error(t('projects.createFailed'), messageFor(cause))
  }
}
</script>

<template>
  <UiCombobox
    v-model="model"
    :items="items"
    :label="t('timer.selectProject')"
    :placeholder="t('timer.project')"
    :none-label="t('timer.noProject')"
    :compact="compact"
    :disabled="disabled"
    creatable
    @create="create"
  />
</template>
