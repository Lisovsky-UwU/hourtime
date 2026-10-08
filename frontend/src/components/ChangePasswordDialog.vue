<script setup lang="ts">
import { computed, ref, useId, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import * as authApi from '@/api/auth'
import { ApiError } from '@/api/client'
import UiButton from '@/components/ui/UiButton.vue'
import UiDialog from '@/components/ui/UiDialog.vue'
import UiField from '@/components/ui/UiField.vue'
import UiInput from '@/components/ui/UiInput.vue'
import { toast } from '@/components/ui/toast'
import { messageFor } from '@/composables/useApiError'

const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{ close: [] }>()

const { t } = useI18n()
const currentErrorId = useId()
const nextErrorId = useId()

const current = ref('')
const next = ref('')
const busy = ref(false)
// Each error sits under the field that has to change.
const currentError = ref<string | null>(null)
const nextError = ref<string | null>(null)

const canSave = computed(() => current.value.length > 0 && next.value.length > 0)

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
    current.value = ''
    next.value = ''
    currentError.value = null
    nextError.value = null
  },
)

async function save() {
  if (!canSave.value || busy.value) return
  busy.value = true
  currentError.value = null
  nextError.value = null
  try {
    await authApi.changePassword(current.value, next.value)
    toast.success(t('settings.passwordChanged'), t('settings.passwordChangedHint'))
    emit('close')
  } catch (error) {
    if (error instanceof ApiError && error.code === 'invalid_current_password') {
      currentError.value = messageFor(error)
    } else {
      nextError.value = messageFor(error)
    }
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <UiDialog v-model:open="model" :title="t('settings.changePassword')">
    <form id="password-form" class="form" @submit.prevent="save">
      <UiField :label="t('settings.currentPassword')">
        <UiInput
          v-model="current"
          type="password"
          autocomplete="current-password"
          required
          :invalid="!!currentError"
          :aria-describedby="currentError ? currentErrorId : undefined"
        />
      </UiField>
      <p v-if="currentError" :id="currentErrorId" class="form-error" role="alert">
        {{ currentError }}
      </p>

      <UiField :label="t('settings.newPassword')" :hint="t('settings.passwordHint')">
        <UiInput
          v-model="next"
          type="password"
          autocomplete="new-password"
          maxlength="128"
          required
          :invalid="!!nextError"
          :aria-describedby="nextError ? nextErrorId : undefined"
        />
      </UiField>
      <p v-if="nextError" :id="nextErrorId" class="form-error" role="alert">{{ nextError }}</p>
    </form>

    <template #footer>
      <UiButton @click="emit('close')">{{ t('common.cancel') }}</UiButton>
      <UiButton type="submit" form="password-form" variant="primary" :disabled="busy || !canSave">
        {{ busy ? t('common.saving') : t('settings.changePassword') }}
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

/* Tucked under its field rather than a full form gap away. */
.form-error {
  margin-top: -10px;
  color: var(--danger);
}
</style>
