<script setup lang="ts">
import { computed, ref, useId, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import ColorPicker from '@/components/ColorPicker.vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiDialog from '@/components/ui/UiDialog.vue'
import UiField from '@/components/ui/UiField.vue'
import UiInput from '@/components/ui/UiInput.vue'
import { useAsyncAction } from '@/composables/useApiError'
import { useProjectsStore } from '@/stores/projects'
import type { Project } from '@/types'
import { nextProjectColor } from '@/utils/projectColors'

/** `project: null` opens the dialog in "create" mode. */
const props = defineProps<{ open: boolean; project: Project | null }>()
const emit = defineEmits<{ close: [] }>()

const { t } = useI18n()
const projects = useProjectsStore()
const { busy, error, run } = useAsyncAction()
const errorId = useId()

const name = ref('')
const color = ref('')

const isEditing = computed(() => props.project !== null)
const canSave = computed(() => name.value.trim().length > 0)

const model = computed({
  get: () => props.open,
  set: (value) => {
    if (!value) emit('close')
  },
})

watch(
  () => [props.open, props.project] as const,
  ([open, project]) => {
    if (!open) return
    error.value = null
    name.value = project?.name ?? ''
    color.value = project?.color ?? nextProjectColor(projects.active.map((item) => item.color))
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
    emit('close')
  })
}
</script>

<template>
  <UiDialog
    v-model:open="model"
    :title="isEditing ? t('projects.form.editTitle') : t('projects.form.createTitle')"
  >
    <form id="project-form" class="form" @submit.prevent="save">
      <UiField :label="t('projects.form.name')">
        <UiInput
          v-model="name"
          maxlength="100"
          :placeholder="t('projects.form.namePlaceholder')"
          required
          :invalid="!!error"
          :aria-describedby="error ? errorId : undefined"
        />
      </UiField>

      <UiField :label="t('projects.form.color')" group>
        <ColorPicker v-model="color" />
      </UiField>

      <p v-if="error" :id="errorId" class="form-error" role="alert">{{ error }}</p>
    </form>

    <template #footer>
      <UiButton @click="emit('close')">{{ t('common.cancel') }}</UiButton>
      <UiButton
        type="submit"
        form="project-form"
        variant="primary"
        :disabled="busy || !canSave"
      >
        {{ busy ? t('common.saving') : isEditing ? t('common.saveChanges') : t('projects.create') }}
      </UiButton>
    </template>
  </UiDialog>
</template>

<style scoped>
.form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-error {
  color: var(--danger);
}
</style>
