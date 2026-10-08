<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import ConfirmDialog from '@/components/ConfirmDialog.vue'
import NameDialog from '@/components/NameDialog.vue'
import UiButton from '@/components/ui/UiButton.vue'
import type { MenuEntry } from '@/components/ui/UiDropdownMenu.vue'
import UiDropdownMenu from '@/components/ui/UiDropdownMenu.vue'
import { toast } from '@/components/ui/toast'
import { messageFor } from '@/composables/useApiError'
import { useEntriesStore } from '@/stores/entries'
import { useTagsStore } from '@/stores/tags'
import type { Tag } from '@/types'

const { t } = useI18n()
const tags = useTagsStore()
const entries = useEntriesStore()
/** Only a failed load shows inline; failed actions go to a toast. */
const loadError = ref<string | null>(null)
const busy = ref(false)

/** `null` while creating; the dialog is open whenever this is not `undefined`. */
const editing = ref<Tag | null | undefined>(undefined)
const pendingDelete = ref<Tag | null>(null)

async function save(name: string) {
  if (editing.value) await tags.rename(editing.value.id, name)
  else await tags.create(name)
}

async function confirmDelete() {
  const tag = pendingDelete.value
  if (!tag) return
  busy.value = true
  try {
    await tags.remove(tag.id)
    pendingDelete.value = null
    // The server took the tag off its entries; the loaded list still has the id.
    if (entries.items.length) await entries.load()
  } catch (cause) {
    // The dialog stays open, so it is clear which deletion failed.
    toast.error(messageFor(cause))
  } finally {
    busy.value = false
  }
}

async function load() {
  loadError.value = null
  try {
    await tags.load()
  } catch (cause) {
    loadError.value = messageFor(cause)
  }
}

function menuFor(tag: Tag): MenuEntry[] {
  return [
    { label: t('common.rename'), icon: 'edit', select: () => (editing.value = tag) },
    'separator',
    {
      label: t('common.delete'),
      icon: 'trash',
      variant: 'danger',
      select: () => (pendingDelete.value = tag),
    },
  ]
}

onMounted(load)
</script>

<template>
  <div class="page list-page">
    <header class="page-head">
      <h1>{{ t('tags.title') }}</h1>
      <UiButton variant="primary" icon="plus" @click="editing = null">
        {{ t('tags.create') }}
      </UiButton>
    </header>

    <div v-if="loadError" class="alert" role="alert">
      <span>{{ t('tags.loadFailed') }} {{ loadError }}</span>
      <UiButton size="sm" @click="load">{{ t('common.retry') }}</UiButton>
    </div>

    <div
      v-else-if="tags.loading && !tags.loaded"
      class="sheet"
      role="status"
      :aria-label="t('common.loading')"
    >
      <div v-for="n in 3" :key="n" class="skeleton-row">
        <span class="skeleton" aria-hidden="true" :style="{ width: `${20 + n * 12}%` }" />
      </div>
    </div>

    <div v-else-if="!tags.items.length" class="empty-state">
      <p class="empty-title">{{ t('tags.emptyTitle') }}</p>
      <p class="muted">{{ t('tags.empty') }}</p>
      <UiButton icon="plus" @click="editing = null">{{ t('tags.create') }}</UiButton>
    </div>

    <table v-else class="sheet data-table">
      <thead>
        <tr>
          <th scope="col">{{ t('tags.name') }}</th>
          <th scope="col" class="actions-col">
            <span class="visually-hidden">{{ t('ui.more') }}</span>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="tag in tags.sorted" :key="tag.id">
          <td>
            <button type="button" class="row-name" @click="editing = tag">
              <span class="row-name-text">{{ tag.name }}</span>
            </button>
          </td>
          <td class="actions-col">
            <UiDropdownMenu :items="menuFor(tag)" :label="t('tags.actionsFor', { name: tag.name })" />
          </td>
        </tr>
      </tbody>
    </table>

    <NameDialog
      :open="editing !== undefined"
      :title="editing ? t('tags.renameTitle') : t('tags.createTitle')"
      :label="t('tags.name')"
      :placeholder="t('tags.namePlaceholder')"
      :initial="editing?.name ?? ''"
      :submit-label="editing ? t('common.saveChanges') : t('tags.create')"
      :save="save"
      @close="editing = undefined"
    />

    <ConfirmDialog
      :open="pendingDelete !== null"
      :title="t('tags.deleteTitle', { name: pendingDelete?.name ?? '' })"
      :message="t('tags.deleteConfirm')"
      :confirm-label="t('tags.deleteAction')"
      :busy="busy"
      @close="pendingDelete = null"
      @confirm="confirmDelete"
    />
  </div>
</template>
