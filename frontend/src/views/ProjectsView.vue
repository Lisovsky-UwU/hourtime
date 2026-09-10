<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import ConfirmDialog from '@/components/ConfirmDialog.vue'
import ProjectDialog from '@/components/ProjectDialog.vue'
import { useAsyncAction } from '@/composables/useApiError'
import { useEntriesStore } from '@/stores/entries'
import { useProjectsStore } from '@/stores/projects'
import type { Project } from '@/types'

const { t } = useI18n()
const projects = useProjectsStore()
const entries = useEntriesStore()
const { busy, error, run } = useAsyncAction()

const editing = ref<Project | null>(null)
const dialogOpen = ref(false)
const pendingDelete = ref<Project | null>(null)
const showArchived = ref(false)

const visible = computed(() =>
  [...projects.items]
    .filter((project) => showArchived.value || !project.archived)
    .sort((a, b) => a.name.localeCompare(b.name)),
)

function openDialog(project: Project | null) {
  editing.value = project
  dialogOpen.value = true
}

async function toggleArchived(project: Project) {
  await run(() => projects.update(project.id, { archived: !project.archived }))
}

async function confirmDelete() {
  const project = pendingDelete.value
  if (!project) return
  await run(async () => {
    await projects.remove(project.id)
    // Entries survive but lose their project, so the list needs a refresh.
    await entries.load()
    pendingDelete.value = null
  })
}

onMounted(() => projects.load())
</script>

<template>
  <div class="page stack">
    <div class="row-between">
      <h1>{{ t('projects.title') }}</h1>
      <div class="row">
        <label class="toggle small">
          <input v-model="showArchived" type="checkbox" />
          {{ t('projects.showArchived') }}
        </label>
        <button type="button" class="btn-primary" @click="openDialog(null)">
          {{ t('projects.new') }}
        </button>
      </div>
    </div>

    <p v-if="error" class="banner">{{ error }}</p>

    <p v-if="!visible.length && !projects.loading" class="card empty">{{ t('projects.empty') }}</p>

    <ul v-else class="card list">
      <li v-for="project in visible" :key="project.id" class="item">
        <span class="dot" :style="{ background: project.color }" />
        <span class="name">{{ project.name }}</span>
        <span v-if="project.archived" class="badge">{{ t('projects.archivedBadge') }}</span>

        <span class="spacer" />

        <button type="button" class="btn-ghost" @click="openDialog(project)">
          {{ t('common.edit') }}
        </button>
        <button type="button" class="btn-ghost" :disabled="busy" @click="toggleArchived(project)">
          {{ project.archived ? t('projects.unarchive') : t('projects.archive') }}
        </button>
        <button type="button" class="btn-ghost danger" @click="pendingDelete = project">
          {{ t('common.delete') }}
        </button>
      </li>
    </ul>

    <ProjectDialog :open="dialogOpen" :project="editing" @close="dialogOpen = false" />

    <ConfirmDialog
      :open="pendingDelete !== null"
      :title="t('common.delete')"
      :message="t('projects.deleteConfirm')"
      :busy="busy"
      @close="pendingDelete = null"
      @confirm="confirmDelete"
    />
  </div>
</template>

<style scoped>
.list {
  list-style: none;
  margin: 0;
  padding: 0;
  overflow: hidden;
}

.item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  border-top: 1px solid var(--border);
}

.item:first-child {
  border-top: none;
}

.name {
  font-weight: 500;
}

.toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  white-space: nowrap;
  color: var(--text-muted);
}

.toggle input {
  width: auto;
}

.danger:hover {
  color: var(--danger);
}
</style>
