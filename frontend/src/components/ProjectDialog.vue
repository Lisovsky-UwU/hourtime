<script setup lang="ts">
import { computed, ref, useId, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import ColorPicker from '@/components/ColorPicker.vue'
import type { ComboboxItem } from '@/components/ui/UiCombobox.vue'
import UiCombobox from '@/components/ui/UiCombobox.vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiDialog from '@/components/ui/UiDialog.vue'
import UiField from '@/components/ui/UiField.vue'
import UiInput from '@/components/ui/UiInput.vue'
import { toast } from '@/components/ui/toast'
import { messageFor, useAsyncAction } from '@/composables/useApiError'
import { useClientsStore } from '@/stores/clients'
import { useProjectsStore } from '@/stores/projects'
import type { Project } from '@/types'
import { nextProjectColor } from '@/utils/projectColors'

/** `project: null` opens the dialog in "create" mode. */
const props = defineProps<{ open: boolean; project: Project | null }>()
const emit = defineEmits<{ close: [] }>()

const { t } = useI18n()
const projects = useProjectsStore()
const clients = useClientsStore()
const { busy, error, run } = useAsyncAction()
const errorId = useId()

const name = ref('')
const color = ref('')
const clientId = ref<string | null>(null)

/** An archived client stays listed only while the project still has it. */
const clientItems = computed<ComboboxItem[]>(() => {
  const current = clients.find(clientId.value)
  const list = current?.archived ? [current, ...clients.active] : clients.active
  return [...list]
    .sort((a, b) => a.name.localeCompare(b.name))
    .map((client) => ({ value: client.id, label: client.name }))
})

async function createClient(clientName: string) {
  try {
    clientId.value = (await clients.create(clientName)).id
  } catch (cause) {
    toast.error(t('clients.createFailed'), messageFor(cause))
  }
}

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
    clientId.value = project?.client_id ?? null
  },
  { immediate: true },
)

async function save() {
  if (!canSave.value) return
  await run(async () => {
    if (props.project) {
      // Re-sending an archived client the project already has would be rejected.
      const clientChanged = clientId.value !== props.project.client_id
      await projects.update(props.project.id, {
        name: name.value.trim(),
        color: color.value,
        ...(clientChanged ? { client_id: clientId.value } : {}),
      })
    } else {
      await projects.create(name.value.trim(), color.value, clientId.value)
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

      <UiField :label="t('projects.form.client')" group>
        <span class="client-picker">
          <UiCombobox
            v-model="clientId"
            :items="clientItems"
            :label="t('projects.form.client')"
            :placeholder="t('projects.form.noClient')"
            :none-label="t('projects.form.noClient')"
            creatable
            @create="createClient"
          />
        </span>
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

.client-picker :deep(.ui-combobox-trigger) {
  width: 100%;
  justify-content: space-between;
  border-color: var(--control-border);
  background: var(--surface);
}

.form-error {
  color: var(--danger);
}
</style>
