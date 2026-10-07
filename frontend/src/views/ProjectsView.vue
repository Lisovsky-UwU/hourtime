<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import ConfirmDialog from '@/components/ConfirmDialog.vue'
import ProjectDialog from '@/components/ProjectDialog.vue'
import UiButton from '@/components/ui/UiButton.vue'
import type { MenuEntry } from '@/components/ui/UiDropdownMenu.vue'
import UiDropdownMenu from '@/components/ui/UiDropdownMenu.vue'
import UiSegmented from '@/components/ui/UiSegmented.vue'
import { toast } from '@/components/ui/toast'
import { messageFor } from '@/composables/useApiError'
import { useEntriesStore } from '@/stores/entries'
import { useProjectsStore } from '@/stores/projects'
import type { Project } from '@/types'

type Filter = 'active' | 'archived'

const { t } = useI18n()
const projects = useProjectsStore()
const entries = useEntriesStore()
/** Only a failed load shows inline; failed actions go to a toast. */
const loadError = ref<string | null>(null)
const busy = ref(false)

const editing = ref<Project | null>(null)
const dialogOpen = ref(false)
const pendingDelete = ref<Project | null>(null)
const filter = ref<Filter>('active')

const filters = computed(() => [
  { value: 'active' as const, label: t('projects.filter.active') },
  { value: 'archived' as const, label: t('projects.filter.archived') },
])

const visible = computed(() =>
  projects.items
    .filter((project) => project.archived === (filter.value === 'archived'))
    .sort((a, b) => a.name.localeCompare(b.name)),
)

function openDialog(project: Project | null) {
  editing.value = project
  dialogOpen.value = true
}

async function toggleArchived(project: Project) {
  try {
    await projects.update(project.id, { archived: !project.archived })
    toast.success(project.archived ? t('projects.restored') : t('projects.archived'), project.name)
  } catch (cause) {
    toast.error(messageFor(cause))
  }
}

async function confirmDelete() {
  const project = pendingDelete.value
  if (!project) return
  busy.value = true
  try {
    await projects.remove(project.id)
    pendingDelete.value = null
    // Entries survive but lose their project, so the list needs a refresh.
    await entries.load()
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
    await projects.load()
  } catch (cause) {
    loadError.value = messageFor(cause)
  }
}

function menuFor(project: Project): MenuEntry[] {
  return [
    { label: t('common.edit'), icon: 'edit', select: () => openDialog(project) },
    {
      label: project.archived ? t('projects.unarchive') : t('projects.archive'),
      icon: project.archived ? 'unarchive' : 'archive',
      select: () => void toggleArchived(project),
    },
    'separator',
    {
      label: t('common.delete'),
      icon: 'trash',
      variant: 'danger',
      select: () => (pendingDelete.value = project),
    },
  ]
}

onMounted(load)
</script>

<template>
  <div class="page">
    <header class="page-head">
      <h1>{{ t('projects.title') }}</h1>
      <UiSegmented v-model="filter" :options="filters" :label="t('projects.filter.label')" />
      <UiButton variant="primary" icon="plus" @click="openDialog(null)">
        {{ t('projects.create') }}
      </UiButton>
    </header>

    <div v-if="loadError" class="alert" role="alert">
      <span>{{ t('projects.loadFailed') }} {{ loadError }}</span>
      <UiButton size="sm" @click="load">{{ t('common.retry') }}</UiButton>
    </div>

    <div
      v-else-if="projects.loading && !projects.loaded"
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
        <p class="empty-title">{{ t('projects.emptyTitle') }}</p>
        <p class="muted">{{ t('projects.empty') }}</p>
        <UiButton icon="plus" @click="openDialog(null)">{{ t('projects.create') }}</UiButton>
      </template>
      <p v-else class="muted">{{ t('projects.emptyArchived') }}</p>
    </div>

    <table v-else class="sheet table">
      <thead>
        <tr>
          <th scope="col">{{ t('projects.form.name') }}</th>
          <th scope="col" class="actions-col">
            <span class="visually-hidden">{{ t('ui.more') }}</span>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="project in visible" :key="project.id">
          <td>
            <button type="button" class="name" @click="openDialog(project)">
              <span class="dot" :style="{ background: project.color }" />
              <span class="name-text">{{ project.name }}</span>
            </button>
          </td>
          <td class="actions-col">
            <UiDropdownMenu
              :items="menuFor(project)"
              :label="t('projects.actionsFor', { name: project.name })"
            />
          </td>
        </tr>
      </tbody>
    </table>

    <ProjectDialog :open="dialogOpen" :project="editing" @close="dialogOpen = false" />

    <ConfirmDialog
      :open="pendingDelete !== null"
      :title="t('projects.deleteTitle', { name: pendingDelete?.name ?? '' })"
      :message="t('projects.deleteConfirm')"
      :confirm-label="t('projects.deleteAction')"
      :busy="busy"
      @close="pendingDelete = null"
      @confirm="confirmDelete"
    />
  </div>
</template>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-top: 28px;
}

.page-head {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.page-head h1 {
  margin-right: auto;
}

.table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

.table th {
  padding: 10px 16px;
  border-bottom: 1px solid var(--border);
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-weight: 500;
  text-align: left;
}

.table td {
  padding: 4px 16px;
  border-top: 1px solid var(--border);
}

.table tbody tr:first-child td {
  border-top: none;
}

.table tbody tr:hover {
  background: var(--surface-muted);
}

.actions-col {
  width: 56px;
  text-align: right;
}

.name {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  max-width: 100%;
  min-height: 40px;
  padding: 0;
  border: 0;
  background: none;
  color: var(--text);
  font: inherit;
  font-weight: 500;
  text-align: left;
  cursor: pointer;
}

.name:hover .name-text {
  text-decoration: underline;
}

.name-text {
  min-width: 0;
  overflow-wrap: anywhere;
}

.dot {
  flex: 0 0 auto;
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.skeleton-row {
  padding: 16px;
  border-top: 1px solid var(--border);
}

.skeleton-row:first-child {
  border-top: none;
}

@media (width < 600px) {
  .page {
    padding-top: 16px;
  }

  .page-head h1 {
    flex-basis: 100%;
  }

  .page-head :deep(.ui-segmented) {
    margin-right: auto;
  }

  .table th,
  .table td {
    padding-inline: 12px;
  }
}
</style>
