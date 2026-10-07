<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import UiButton from '@/components/ui/UiButton.vue'
import UiDialog from '@/components/ui/UiDialog.vue'

/**
 * Used instead of `window.confirm` so the prompt is themed, translatable and
 * does not freeze the page.
 */
const props = defineProps<{
  open: boolean
  title: string
  message: string
  /** Names the action, e.g. "Delete entry"; the button never just says "OK". */
  confirmLabel: string
  busy?: boolean
}>()
const emit = defineEmits<{ close: []; confirm: [] }>()

const { t } = useI18n()

const model = computed({
  get: () => props.open,
  set: (value) => {
    if (!value) emit('close')
  },
})
</script>

<template>
  <UiDialog v-model:open="model" :title="title" :description="message">
    <template #footer>
      <UiButton @click="emit('close')">{{ t('common.cancel') }}</UiButton>
      <UiButton variant="danger-solid" :disabled="busy" @click="emit('confirm')">
        {{ confirmLabel }}
      </UiButton>
    </template>
  </UiDialog>
</template>
