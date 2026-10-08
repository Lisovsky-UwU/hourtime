<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import ConfirmDialog from '@/components/ConfirmDialog.vue'
import NameDialog from '@/components/NameDialog.vue'
import UiButton from '@/components/ui/UiButton.vue'
import type { MenuEntry } from '@/components/ui/UiDropdownMenu.vue'
import UiDropdownMenu from '@/components/ui/UiDropdownMenu.vue'
import UiSegmented from '@/components/ui/UiSegmented.vue'
import { toast } from '@/components/ui/toast'
import { messageFor } from '@/composables/useApiError'
import { useClientsStore } from '@/stores/clients'
import { useProjectsStore } from '@/stores/projects'
import type { Client } from '@/types'

type Filter = 'active' | 'archived'

const { t } = useI18n()
const clients = useClientsStore()
const projects = useProjectsStore()
/** Only a failed load shows inline; failed actions go to a toast. */
const loadError = ref<string | null>(null)
const busy = ref(false)

/** `null` while creating; the dialog is open whenever this is not `undefined`. */
const editing = ref<Client | null | undefined>(undefined)
const pendingDelete = ref<Client | null>(null)
const filter = ref<Filter>('active')

const filters = computed(() => [
  { value: 'active' as const, label: t('clients.filter.active') },
  { value: 'archived' as const, label: t('clients.filter.archived') },
])

const visible = computed(() =>
  clients.items
    .filter((client) => client.archived === (filter.value === 'archived'))
    .sort((a, b) => a.name.localeCompare(b.name)),
)

/** Live projects per client; archived ones are out of sight on the projects page too. */
const projectCounts = computed(() => {
  const counts = new Map<string, number>()
  for (const project of projects.active) {
    if (project.client_id) counts.set(project.client_id, (counts.get(project.client_id) ?? 0) + 1)
  }
  return counts
})

async function save(name: string) {
  if (editing.value) await clients.update(editing.value.id, { name })
  else await clients.create(name)
}

async function toggleArchived(client: Client) {
  try {
    await clients.update(client.id, { archived: !client.archived })
    toast.success(client.archived ? t('clients.restored') : t('clients.archived'), client.name)
  } catch (cause) {
    toast.error(messageFor(cause))
  }
}

async function confirmDelete() {
  const client = pendingDelete.value
  if (!client) return
  busy.value = true
  try {
    await clients.remove(client.id)
    pendingDelete.value = null
    // Its projects stay but lose the client.
    await projects.load(true)
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
    await Promise.all([clients.load(), projects.load()])
  } catch (cause) {
    loadError.value = messageFor(cause)
  }
}

function menuFor(client: Client): MenuEntry[] {
  return [
    { label: t('common.rename'), icon: 'edit', select: () => (editing.value = client) },
    {
      label: client.archived ? t('clients.unarchive') : t('clients.archive'),
      icon: client.archived ? 'unarchive' : 'archive',
      select: () => void toggleArchived(client),
    },
    'separator',
    {
      label: t('common.delete'),
      icon: 'trash',
      variant: 'danger',
      select: () => (pendingDelete.value = client),
    },
  ]
}

onMounted(load)
</script>

<template>
  <div class="page list-page">
    <header class="page-head">
      <h1>{{ t('clients.title') }}</h1>
      <UiSegmented v-model="filter" :options="filters" :label="t('clients.filter.label')" />
      <UiButton variant="primary" icon="plus" @click="editing = null">
        {{ t('clients.create') }}
      </UiButton>
    </header>

    <div v-if="loadError" class="alert" role="alert">
      <span>{{ t('clients.loadFailed') }} {{ loadError }}</span>
      <UiButton size="sm" @click="load">{{ t('common.retry') }}</UiButton>
    </div>

    <div
      v-else-if="clients.loading && !clients.loaded"
      class="sheet"
      role="status"
      :aria-label="t('common.loading')"
    >
      <div v-for="n in 3" :key="n" class="skeleton-row">
        <span class="skeleton" aria-hidden="true" :style="{ width: `${20 + n * 12}%` }" />
      </div>
    </div>

    <div v-else-if="!visible.length" class="empty-state">
      <template v-if="filter === 'active'">
        <p class="empty-title">{{ t('clients.emptyTitle') }}</p>
        <p class="muted">{{ t('clients.empty') }}</p>
        <UiButton icon="plus" @click="editing = null">{{ t('clients.create') }}</UiButton>
      </template>
      <p v-else class="muted">{{ t('clients.emptyArchived') }}</p>
    </div>

    <table v-else class="sheet data-table">
      <thead>
        <tr>
          <th scope="col">{{ t('clients.name') }}</th>
          <th scope="col" class="num-col">{{ t('clients.projects') }}</th>
          <th scope="col" class="actions-col">
            <span class="visually-hidden">{{ t('ui.more') }}</span>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="client in visible" :key="client.id">
          <td>
            <button type="button" class="row-name" @click="editing = client">
              <span class="row-name-text">{{ client.name }}</span>
            </button>
          </td>
          <td class="num-col num">{{ projectCounts.get(client.id) ?? 0 }}</td>
          <td class="actions-col">
            <UiDropdownMenu
              :items="menuFor(client)"
              :label="t('clients.actionsFor', { name: client.name })"
            />
          </td>
        </tr>
      </tbody>
    </table>

    <NameDialog
      :open="editing !== undefined"
      :title="editing ? t('clients.renameTitle') : t('clients.createTitle')"
      :label="t('clients.name')"
      :placeholder="t('clients.namePlaceholder')"
      :initial="editing?.name ?? ''"
      :submit-label="editing ? t('common.saveChanges') : t('clients.create')"
      :save="save"
      @close="editing = undefined"
    />

    <ConfirmDialog
      :open="pendingDelete !== null"
      :title="t('clients.deleteTitle', { name: pendingDelete?.name ?? '' })"
      :message="t('clients.deleteConfirm')"
      :confirm-label="t('clients.deleteAction')"
      :busy="busy"
      @close="pendingDelete = null"
      @confirm="confirmDelete"
    />
  </div>
</template>
