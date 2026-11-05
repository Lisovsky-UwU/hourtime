<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'

import AppIcon from '@/components/AppIcon.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import ProjectDialog from '@/components/ProjectDialog.vue'
import TaskDialog from '@/components/TaskDialog.vue'
import UiButton from '@/components/ui/UiButton.vue'
import type { MenuEntry } from '@/components/ui/UiDropdownMenu.vue'
import UiDropdownMenu from '@/components/ui/UiDropdownMenu.vue'
import UiSegmented from '@/components/ui/UiSegmented.vue'
import { toast } from '@/components/ui/toast'
import { messageFor } from '@/composables/useApiError'
import { useDuration } from '@/composables/useDuration'
import { useClientsStore } from '@/stores/clients'
import { useProjectsStore } from '@/stores/projects'
import { useTasksStore } from '@/stores/tasks'
import { useWorkspaceStore } from '@/stores/workspace'
import type { Project, Task } from '@/types'

type Filter = 'active' | 'completed'

const route = useRoute()
const { t } = useI18n()
const projects = useProjectsStore()
const tasks = useTasksStore()
const clients = useClientsStore()
const workspace = useWorkspaceStore()
const duration = useDuration()

const projectId = computed(() => String(route.params.projectId ?? ''))
const project = computed(() => projects.find(projectId.value))
const isArchived = computed(() => project.value?.archived ?? false)
/** Tasks of an archived project are history: nothing may change them. */
const canManage = computed(() => workspace.canManage && !isArchived.value)
const canCreate = computed(() => !isArchived.value)

const filter = ref<Filter>('active')
const filters = computed(() => [
  { value: 'active' as const, label: t('tasks.filter.active') },
  { value: 'completed' as const, label: t('tasks.filter.completed') },
])

const visible = computed(() => tasks.sortedOf(projectId.value, filter.value === 'completed'))

/** Only a failed load shows inline; failed actions go to a toast. */
const loadError = ref<string | null>(null)
const busy = ref(false)
const taskDialogOpen = ref(false)
const editingTask = ref<Task | null>(null)
const pendingDelete = ref<Task | null>(null)
const projectDialogOpen = ref(false)

async function load() {
  loadError.value = null
  try {
    await Promise.all([projects.load(), clients.load(), workspace.load()])
    if (project.value) await tasks.load(projectId.value)
  } catch (cause) {
    loadError.value = messageFor(cause)
  }
}

async function toggleCompleted(task: Task) {
  try {
    await tasks.setCompleted(task.id, !task.completed)
    toast.success(task.completed ? t('tasks.reopened') : t('tasks.completed'), task.name)
  } catch (cause) {
    toast.error(messageFor(cause))
  }
}

async function confirmDelete() {
  const task = pendingDelete.value
  if (!task) return
  busy.value = true
  try {
    await tasks.remove(task.id)
    pendingDelete.value = null
  } catch (cause) {
    // The dialog stays open, so it is clear which deletion failed.
    toast.error(messageFor(cause))
  } finally {
    busy.value = false
  }
}

async function toggleArchived() {
  const current = project.value
  if (!current) return
  try {
    await projects.update(current.id, { archived: !current.archived })
    toast.success(
      current.archived ? t('projects.restored') : t('projects.archived'),
      current.name,
    )
  } catch (cause) {
    toast.error(messageFor(cause))
  }
}

function openTask(task: Task | null) {
  editingTask.value = task
  taskDialogOpen.value = true
}

function taskMenu(task: Task): MenuEntry[] {
  return [
    { label: t('common.edit'), icon: 'edit', select: () => openTask(task) },
    {
      label: task.completed ? t('tasks.reopen') : t('tasks.complete'),
      icon: task.completed ? 'unarchive' : 'check',
      select: () => void toggleCompleted(task),
    },
    'separator',
    {
      label: t('common.delete'),
      icon: 'trash',
      variant: 'danger',
      select: () => (pendingDelete.value = task),
    },
  ]
}

const projectMenu = computed<MenuEntry[]>(() => {
  const current: Project | undefined = project.value
  if (!current) return []
  return [
    {
      label: t('projects.form.editTitle'),
      icon: 'edit',
      select: () => (projectDialogOpen.value = true),
    },
    {
      label: current.archived ? t('projects.unarchive') : t('projects.archive'),
      icon: current.archived ? 'unarchive' : 'archive',
      select: () => void toggleArchived(),
    },
  ]
})

watch(
  projectId,
  () => {
    filter.value = 'active'
    void load()
  },
  { immediate: true },
)
</script>

<template>
  <div class="page list-page">
    <RouterLink class="back" :to="{ name: 'projects' }">
      <AppIcon name="chevron-left" :size="16" />
      {{ t('tasks.back') }}
    </RouterLink>

    <div v-if="loadError" class="alert" role="alert">
      <span>{{ t('tasks.loadFailed') }} {{ loadError }}</span>
      <UiButton size="sm" @click="load">{{ t('common.retry') }}</UiButton>
    </div>

    <template v-else-if="project">
      <header class="page-head">
        <h1 class="project-title">
          <span class="row-dot" :style="{ background: project.color }" />
          {{ project.name }}
        </h1>
        <UiSegmented v-model="filter" :options="filters" :label="t('tasks.filter.label')" />
        <UiButton v-if="canCreate" variant="primary" icon="plus" @click="openTask(null)">
          {{ t('tasks.create') }}
        </UiButton>
        <UiDropdownMenu
          v-if="workspace.canManage"
          :items="projectMenu"
          :label="t('projects.actionsFor', { name: project.name })"
        />
      </header>

      <p class="project-meta muted">
        {{ project.client_id ? clients.find(project.client_id)?.name : t('projects.form.noClient') }}
        <span v-if="isArchived" class="archived-tag">{{ t('tasks.archivedTag') }}</span>
      </p>

      <p v-if="isArchived" class="note">
        {{ t('tasks.archivedHint') }}
        <UiButton v-if="workspace.canManage" size="sm" @click="toggleArchived">
          {{ t('tasks.archivedRestore') }}
        </UiButton>
      </p>

      <div
        v-if="tasks.loading && !tasks.loaded(projectId)"
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
          <p class="empty-title">{{ t('tasks.emptyTitle') }}</p>
          <p class="muted">{{ t('tasks.empty') }}</p>
          <UiButton v-if="canCreate" icon="plus" @click="openTask(null)">
            {{ t('tasks.create') }}
          </UiButton>
        </template>
        <p v-else class="muted">{{ t('tasks.emptyCompleted') }}</p>
      </div>

      <table v-else class="sheet data-table">
        <thead>
          <tr>
            <th scope="col">{{ t('tasks.name') }}</th>
            <th scope="col" class="num-col">{{ t('tasks.estimate') }}</th>
            <th v-if="canManage" scope="col" class="actions-col">
              <span class="visually-hidden">{{ t('ui.more') }}</span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="task in visible" :key="task.id" :data-completed="task.completed ? '' : undefined">
            <td>
              <button v-if="canManage" type="button" class="row-name" @click="openTask(task)">
                <span v-if="task.completed" class="done-mark" aria-hidden="true">
                  <AppIcon name="check" :size="14" />
                </span>
                <span class="row-name-text">{{ task.name }}</span>
              </button>
              <span v-else class="row-name">
                <span v-if="task.completed" class="done-mark" aria-hidden="true">
                  <AppIcon name="check" :size="14" />
                </span>
                <span class="row-name-text">{{ task.name }}</span>
              </span>
            </td>
            <td class="num-col num estimate">
              {{ task.estimated_seconds ? duration(task.estimated_seconds) : '' }}
            </td>
            <td v-if="canManage" class="actions-col">
              <UiDropdownMenu
                :items="taskMenu(task)"
                :label="t('tasks.actionsFor', { name: task.name })"
              />
            </td>
          </tr>
        </tbody>
      </table>
    </template>

    <div v-else-if="!projects.loading" class="empty-state">
      <p class="empty-title">{{ t('tasks.notFound') }}</p>
      <RouterLink :to="{ name: 'projects' }" class="back">
        <AppIcon name="chevron-left" :size="16" />
        {{ t('tasks.notFoundBack') }}
      </RouterLink>
    </div>

    <TaskDialog
      v-if="project"
      :open="taskDialogOpen"
      :project-id="project.id"
      :task="editingTask"
      @close="taskDialogOpen = false"
    />

    <ProjectDialog
      v-if="project"
      :open="projectDialogOpen"
      :project="project"
      @close="projectDialogOpen = false"
    />

    <ConfirmDialog
      :open="pendingDelete !== null"
      :title="t('tasks.deleteTitle', { name: pendingDelete?.name ?? '' })"
      :message="t('tasks.deleteConfirm')"
      :confirm-label="t('tasks.deleteAction')"
      :busy="busy"
      @close="pendingDelete = null"
      @confirm="confirmDelete"
    />
  </div>
</template>

<style scoped>
.back {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  align-self: flex-start;
  color: var(--text-muted);
  font-size: var(--text-sm);
  text-decoration: none;
}

.back:hover {
  color: var(--text);
  text-decoration: underline;
}

.project-title {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  overflow-wrap: anywhere;
}

.project-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: -8px;
}

/* The archive mark is a stamp, like the running timer: a state, not decoration. */
.archived-tag {
  padding: 2px 8px;
  border: 1px solid var(--control-border);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
}

.note {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px 12px;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--surface-muted);
  color: var(--text-muted);
}

/* A finished task is history: pencil, with a check mark instead of a strike. */
.data-table tr[data-completed] .row-name-text,
.data-table tr[data-completed] .estimate {
  color: var(--text-muted);
}

.done-mark {
  display: inline-flex;
  color: var(--accent);
}
</style>
