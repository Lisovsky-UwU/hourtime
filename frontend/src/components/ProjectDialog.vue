<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseDialog from '@/components/BaseDialog.vue'
import ColorPicker from '@/components/ColorPicker.vue'
import { useAsyncAction } from '@/composables/useApiError'
import { useProjectsStore } from '@/stores/projects'
import type { Project } from '@/types'

const DEFAULT_COLOR = '#4285f4'

/** `project: null` opens the dialog in "create" mode. */
const props = defineProps<{ open: boolean; project: Project | null }>()
const emit = defineEmits<{ close: []; saved: [] }>()

const { t } = useI18n()
const projects = useProjectsStore()
const { busy, error, run } = useAsyncAction()

const name = ref('')
const color = ref(DEFAULT_COLOR)

const isEditing = computed(() => props.project !== null)
const canSave = computed(() => name.value.trim().length > 0)

watch(
  () => [props.open, props.project] as const,
  ([open, project]) => {
    if (!open) return
    error.value = null
    name.value = project?.name ?? ''
    color.value = project?.color ?? DEFAULT_COLOR
  },
  { immediate: true },
)

async function save() {
  if (!canSave.value) return
  await run(async () => {
    if (props.project) {
      await projects.update(props.project.id, { name: name.value.trim(), color: color.value })
    } else {
      await projects.create(name.value.trim(), color.value)
    }
    emit('saved')
    emit('close')
  })
}
</script>

<template>
  <BaseDialog
    :open="open"
    :title="isEditing ? t('projects.form.editTitle') : t('projects.form.createTitle')"
    @close="emit('close')"
  >
    <div class="field">
      <label for="project-name">{{ t('projects.form.name') }}</label>
      <input
        id="project-name"
        v-model="name"
        type="text"
        maxlength="100"
        :placeholder="t('projects.form.namePlaceholder')"
        @keyup.enter="save"
      />
    </div>

    <div class="field">
      <label>{{ t('projects.form.color') }}</label>
      <ColorPicker v-model="color" />
    </div>

    <p v-if="error" class="banner">{{ error }}</p>

    <div class="row-between">
      <span class="spacer" />
      <button type="button" @click="emit('close')">{{ t('common.cancel') }}</button>
      <button type="button" class="btn-primary" :disabled="busy || !canSave" @click="save">
        {{ busy ? t('common.saving') : t('common.save') }}
      </button>
    </div>
  </BaseDialog>
</template>
