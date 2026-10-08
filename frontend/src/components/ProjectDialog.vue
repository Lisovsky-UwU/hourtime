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
import UiSwitch from '@/components/ui/UiSwitch.vue'
import { toast } from '@/components/ui/toast'
import { messageFor, useAsyncAction } from '@/composables/useApiError'
import { useBilling } from '@/composables/useBilling'
import { useClientsStore } from '@/stores/clients'
import { useProjectsStore } from '@/stores/projects'
import { useWorkspaceStore } from '@/stores/workspace'
import type { Project } from '@/types'
import { parseRate, rateForInput } from '@/utils/money'
import { nextProjectColor } from '@/utils/projectColors'

/** `project: null` opens the dialog in "create" mode. */
const props = defineProps<{ open: boolean; project: Project | null }>()
const emit = defineEmits<{ close: [] }>()

const { t, locale } = useI18n()
const projects = useProjectsStore()
const clients = useClientsStore()
const workspace = useWorkspaceStore()
const billing = useBilling()
const { busy, error, run } = useAsyncAction()
const errorId = useId()
const rateErrorId = useId()

const name = ref('')
const color = ref('')
const clientId = ref<string | null>(null)
const billable = ref(false)
const rate = ref('')
const rateError = ref<string | null>(null)

/** What an empty rate means, so the field explains itself. */
const rateHint = computed(() =>
  workspace.defaultRateCents === null
    ? t('billing.projectRateNoDefault')
    : t('billing.projectRateHint', { rate: billing.money(workspace.defaultRateCents) }),
)

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
    billable.value = project?.billable ?? false
    rate.value = rateForInput(project?.hourly_rate ?? null, locale.value)
    rateError.value = null
  },
  { immediate: true },
)

async function save() {
  if (!canSave.value) return
  const hourlyRate = parseRate(rate.value)
  if (hourlyRate === undefined) {
    rateError.value = t('billing.rateInvalid')
    return
  }
  rateError.value = null
  await run(async () => {
    if (props.project) {
      // Re-sending an archived client the project already has would be rejected.
      const clientChanged = clientId.value !== props.project.client_id
      await projects.update(props.project.id, {
        name: name.value.trim(),
        color: color.value,
        billable: billable.value,
        hourly_rate: hourlyRate,
        ...(clientChanged ? { client_id: clientId.value } : {}),
      })
    } else {
      await projects.create(name.value.trim(), color.value, {
        client_id: clientId.value,
        billable: billable.value,
        hourly_rate: hourlyRate,
      })
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

      <div class="billing">
        <UiSwitch
          v-model="billable"
          :label="t('billing.projectBillable')"
          :hint="t('billing.projectBillableHint')"
        />

        <UiField :label="t('billing.hourlyRate')" :hint="rateHint">
          <span class="rate">
            <UiInput
              v-model="rate"
              inputmode="decimal"
              autocomplete="off"
              class="num"
              :placeholder="t('billing.ratePlaceholder')"
              :invalid="!!rateError"
              :aria-describedby="rateError ? rateErrorId : undefined"
            />
            <span class="rate-unit">{{ t('billing.perHour', { currency: billing.symbol.value }) }}</span>
          </span>
        </UiField>
        <p v-if="rateError" :id="rateErrorId" class="form-error" role="alert">{{ rateError }}</p>
      </div>

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

/* Billing sits apart from naming: a rule above says it is a different concern. */
.billing {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
}

.rate {
  display: flex;
  align-items: center;
  gap: 8px;
}

.rate :deep(.ui-input) {
  flex: 0 1 160px;
  text-align: right;
}

.rate-unit {
  color: var(--text-muted);
  white-space: nowrap;
}
</style>
