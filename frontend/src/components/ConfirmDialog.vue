<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import BaseDialog from '@/components/BaseDialog.vue'

/**
 * Used instead of `window.confirm` so the prompt is themed, translatable and
 * does not freeze the page.
 */
defineProps<{ open: boolean; title: string; message: string; busy?: boolean }>()
const emit = defineEmits<{ close: []; confirm: [] }>()

const { t } = useI18n()
</script>

<template>
  <BaseDialog :open="open" :title="title" @close="emit('close')">
    <p class="message">{{ message }}</p>

    <div class="row-between">
      <span class="spacer" />
      <button type="button" @click="emit('close')">{{ t('common.cancel') }}</button>
      <button type="button" class="btn-danger" :disabled="busy" @click="emit('confirm')">
        {{ t('common.delete') }}
      </button>
    </div>
  </BaseDialog>
</template>

<style scoped>
.message {
  margin: 0;
  color: var(--text-muted);
}
</style>
