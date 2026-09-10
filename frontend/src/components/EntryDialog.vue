<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import type { EntryPatch } from '@/api/timeEntries'
import BaseDialog from '@/components/BaseDialog.vue'
import ProjectPicker from '@/components/ProjectPicker.vue'
import { useAsyncAction } from '@/composables/useApiError'
import { useEntriesStore } from '@/stores/entries'
import { useTimerStore } from '@/stores/timer'
import type { TimeEntry } from '@/types'
import { DATETIME_STEP, fromLocalInput, toLocalInput } from '@/utils/datetime'
import { formatCompact } from '@/utils/duration'
import { serverNowIso } from '@/utils/serverTime'

/** `entry: null` means "add an entry by hand" rather than "edit this one". */
const props = defineProps<{ open: boolean; entry: TimeEntry | null }>()
const emit = defineEmits<{ close: [] }>()

const { t } = useI18n()
const entries = useEntriesStore()
const timer = useTimerStore()
const { busy, error, run } = useAsyncAction()

const description = ref('')
const projectId = ref<string | null>(null)
const startedAt = ref('')
const stoppedAt = ref('')

const isEditing = computed(() => props.entry !== null)
const wasRunning = computed(() => props.entry !== null && props.entry.stopped_at === null)

const previewSeconds = computed(() => {
  const from = fromLocalInput(startedAt.value)
  const to = fromLocalInput(stoppedAt.value)
  if (!from || !to) return null
  return Math.max(0, Math.floor((Date.parse(to) - Date.parse(from)) / 1000))
})

watch(
  () => [props.open, props.entry] as const,
  ([open, entry]) => {
    if (!open) return
    error.value = null
    description.value = entry?.description ?? ''
    projectId.value = entry?.project_id ?? null
    startedAt.value = toLocalInput(entry?.started_at ?? serverNowIso())
    stoppedAt.value = entry?.stopped_at ? toLocalInput(entry.stopped_at) : ''
  },
  { immediate: true },
)

async function save() {
  const startedIso = fromLocalInput(startedAt.value)
  const stoppedIso = fromLocalInput(stoppedAt.value)
  if (!startedIso) return

  await run(async () => {
    if (!props.entry) {
      if (!stoppedIso) return
      await entries.create({
        started_at: startedIso,
        stopped_at: stoppedIso,
        project_id: projectId.value,
        description: description.value,
      })
    } else {
      const patch: EntryPatch = {
        description: description.value,
        project_id: projectId.value,
        started_at: startedIso,
      }
      if (stoppedIso) patch.stopped_at = stoppedIso
      const updated = await entries.update(props.entry.id, patch)
      // Editing the entry that is currently running changes what the timer bar
      // shows — and giving it an end time stops it.
      timer.applySaved(updated)
    }
    emit('close')
  })
}
</script>

<template>
  <BaseDialog
    :open="open"
    :title="isEditing ? t('entries.edit.title') : t('entries.edit.createTitle')"
    @close="emit('close')"
  >
    <div class="field">
      <label for="entry-description">{{ t('entries.edit.description') }}</label>
      <input
        id="entry-description"
        v-model="description"
        type="text"
        :placeholder="t('entries.edit.descriptionPlaceholder')"
      />
    </div>

    <div class="field">
      <label for="entry-project">{{ t('entries.edit.project') }}</label>
      <ProjectPicker v-model="projectId" :aria-label="t('entries.edit.project')" />
    </div>

    <div class="times">
      <div class="field">
        <label for="entry-start">{{ t('entries.edit.startedAt') }}</label>
        <input
          id="entry-start"
          v-model="startedAt"
          type="datetime-local"
          :step="DATETIME_STEP"
          required
        />
      </div>
      <div class="field">
        <label for="entry-stop">{{ t('entries.edit.stoppedAt') }}</label>
        <input
          id="entry-stop"
          v-model="stoppedAt"
          type="datetime-local"
          :step="DATETIME_STEP"
          :required="!isEditing"
        />
      </div>
    </div>

    <p v-if="wasRunning" class="muted small">{{ t('entries.edit.stillRunning') }}</p>

    <p v-if="previewSeconds !== null" class="muted small">
      {{ t('entries.edit.duration') }}:
      <span class="mono">{{ formatCompact(previewSeconds) }}</span>
    </p>

    <p v-if="error" class="banner">{{ error }}</p>

    <div class="row-between">
      <span class="spacer" />
      <button type="button" @click="emit('close')">{{ t('common.cancel') }}</button>
      <button type="button" class="btn-primary" :disabled="busy" @click="save">
        {{ busy ? t('common.saving') : t('common.save') }}
      </button>
    </div>
  </BaseDialog>
</template>

<style scoped>
.times {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

@media (width <= 480px) {
  .times {
    grid-template-columns: 1fr;
  }
}
</style>
