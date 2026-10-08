<script setup lang="ts">
import { computed, ref, useId, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import UiButton from '@/components/ui/UiButton.vue'
import UiDialog from '@/components/ui/UiDialog.vue'
import UiField from '@/components/ui/UiField.vue'
import UiInput from '@/components/ui/UiInput.vue'
import { useAsyncAction } from '@/composables/useApiError'

/**
 * Create or rename something that is only a name - a client or a tag.
 * The caller does the saving; a rejected name keeps the dialog open with the
 * reason under the field.
 */
const props = defineProps<{
  open: boolean
  title: string
  label: string
  placeholder: string
  /** Empty in "create" mode. */
  initial: string
  submitLabel: string
  save: (name: string) => Promise<unknown>
}>()
const emit = defineEmits<{ close: [] }>()

const { t } = useI18n()
const { busy, error, run } = useAsyncAction()
const errorId = useId()
const formId = useId()

const name = ref('')
const canSave = computed(() => name.value.trim().length > 0)

const model = computed({
  get: () => props.open,
  set: (value) => {
    if (!value) emit('close')
  },
})

watch(
  () => props.open,
  (open) => {
    if (!open) return
    error.value = null
    name.value = props.initial
  },
  { immediate: true },
)

async function submit() {
  if (!canSave.value) return
  const trimmed = name.value.trim()
  if (trimmed === props.initial) {
    emit('close')
    return
  }
  await run(async () => {
    await props.save(trimmed)
    emit('close')
  })
}
</script>

<template>
  <UiDialog v-model:open="model" :title="title">
    <form :id="formId" class="form" @submit.prevent="submit">
      <UiField :label="label">
        <UiInput
          v-model="name"
          maxlength="100"
          :placeholder="placeholder"
          required
          :invalid="!!error"
          :aria-describedby="error ? errorId : undefined"
        />
      </UiField>
      <p v-if="error" :id="errorId" class="form-error" role="alert">{{ error }}</p>
    </form>

    <template #footer>
      <UiButton @click="emit('close')">{{ t('common.cancel') }}</UiButton>
      <UiButton type="submit" :form="formId" variant="primary" :disabled="busy || !canSave">
        {{ busy ? t('common.saving') : submitLabel }}
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

.form-error {
  color: var(--danger);
}
</style>
