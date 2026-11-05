<script setup lang="ts">
import { computed, ref, useId, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import UiButton from '@/components/ui/UiButton.vue'
import UiDialog from '@/components/ui/UiDialog.vue'
import UiField from '@/components/ui/UiField.vue'
import UiInput from '@/components/ui/UiInput.vue'
import { useAsyncAction } from '@/composables/useApiError'
import { useTasksStore } from '@/stores/tasks'
import type { Task } from '@/types'
import { formatClock, parseDurationText } from '@/utils/duration'

/**
 * Create or edit a task: a name and an optional estimate. `task: null` opens
 * the dialog in "create" mode.
 */
const props = defineProps<{ open: boolean; projectId: string; task: Task | null }>()
const emit = defineEmits<{ close: [] }>()

const { t } = useI18n()
const tasks = useTasksStore()
const { busy, error, run } = useAsyncAction()
const errorId = useId()
const estimateErrorId = useId()
const formId = useId()

const name = ref('')
const estimate = ref('')
const estimateError = ref<string | null>(null)

const isEditing = computed(() => props.task !== null)
const canSave = computed(() => name.value.trim().length > 0)

const model = computed({
  get: () => props.open,
  set: (value) => {
    if (!value) emit('close')
  },
})

watch(
  () => [props.open, props.task] as const,
  ([open, task]) => {
    if (!open) return
    error.value = null
    name.value = task?.name ?? ''
    // Always `H:MM` in the field, whatever the profile's display format: it
    // reads back the same way and the parser accepts it for any length.
    estimate.value = task?.estimated_seconds ? formatClock(task.estimated_seconds) : ''
    estimateError.value = null
  },
  { immediate: true },
)

/** Empty clears the estimate; anything unparseable or zero is an error. */
function parseEstimate(text: string): number | null | undefined {
  if (!text.trim()) return null
  const seconds = parseDurationText(text)
  return seconds !== null && seconds > 0 ? seconds : undefined
}

async function save() {
  if (!canSave.value) return
  const estimatedSeconds = parseEstimate(estimate.value)
  if (estimatedSeconds === undefined) {
    estimateError.value = t('tasks.estimateInvalid')
    return
  }
  estimateError.value = null
  await run(async () => {
    if (props.task) {
      await tasks.update(props.task.id, {
        name: name.value.trim(),
        estimated_seconds: estimatedSeconds,
      })
    } else {
      await tasks.create(props.projectId, name.value.trim(), estimatedSeconds)
    }
    emit('close')
  })
}
</script>

<template>
  <UiDialog v-model:open="model" :title="isEditing ? t('tasks.editTitle') : t('tasks.createTitle')">
    <form :id="formId" class="form" @submit.prevent="save">
      <UiField :label="t('tasks.name')">
        <UiInput
          v-model="name"
          maxlength="100"
          :placeholder="t('tasks.namePlaceholder')"
          required
          :invalid="!!error"
          :aria-describedby="error ? errorId : undefined"
        />
      </UiField>

      <UiField :label="t('tasks.estimate')" :hint="t('tasks.estimateHint')">
        <UiInput
          v-model="estimate"
          inputmode="decimal"
          autocomplete="off"
          class="num estimate"
          :placeholder="t('tasks.estimatePlaceholder')"
          :invalid="!!estimateError"
          :aria-describedby="estimateError ? estimateErrorId : undefined"
        />
      </UiField>
      <p v-if="estimateError" :id="estimateErrorId" class="form-error" role="alert">
        {{ estimateError }}
      </p>

      <p v-if="error" :id="errorId" class="form-error" role="alert">{{ error }}</p>
    </form>

    <template #footer>
      <UiButton @click="emit('close')">{{ t('common.cancel') }}</UiButton>
      <UiButton type="submit" :form="formId" variant="primary" :disabled="busy || !canSave">
        {{ busy ? t('common.saving') : isEditing ? t('common.saveChanges') : t('tasks.create') }}
      </UiButton>
    </template>
  </UiDialog>
</template>

<style scoped>
.form {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.estimate {
  width: 100%;
  max-width: 200px;
  text-align: right;
}

.form-error {
  color: var(--danger);
}
</style>
