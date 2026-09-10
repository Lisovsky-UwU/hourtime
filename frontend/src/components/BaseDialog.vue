<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps<{ open: boolean; title: string }>()
const emit = defineEmits<{ close: [] }>()

const { t } = useI18n()
const dialog = ref<HTMLDialogElement | null>(null)

// Native <dialog> gives focus trapping, Esc handling and the backdrop for free.
watch(
  () => props.open,
  async (open) => {
    await nextTick()
    const element = dialog.value
    if (!element) return
    if (open && !element.open) element.showModal()
    if (!open && element.open) element.close()
  },
  { immediate: true },
)
</script>

<template>
  <!-- Esc and the explicit buttons close it; a stray backdrop click must not
       throw away what the user typed. -->
  <dialog ref="dialog" @cancel.prevent="emit('close')">
    <form method="dialog" class="dialog-body" @submit.prevent>
      <div class="row-between dialog-head">
        <h2>{{ title }}</h2>
        <button
          type="button"
          class="btn-ghost"
          :aria-label="t('common.close')"
          @click="emit('close')"
        >
          ✕
        </button>
      </div>

      <slot />
    </form>
  </dialog>
</template>

<style scoped>
dialog {
  padding: 0;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--surface);
  color: var(--text);
  box-shadow: var(--shadow);
  width: min(460px, calc(100vw - 32px));
}

dialog::backdrop {
  background: rgb(0 0 0 / 45%);
}

.dialog-body {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 18px;
}

.dialog-head {
  align-items: flex-start;
}
</style>
