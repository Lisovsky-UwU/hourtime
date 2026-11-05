<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  ListboxContent,
  ListboxFilter,
  ListboxGroup,
  ListboxGroupLabel,
  ListboxItem,
  ListboxItemIndicator,
  ListboxRoot,
  PopoverContent,
  PopoverPortal,
  PopoverRoot,
  PopoverTrigger,
} from 'reka-ui'

import AppIcon from '@/components/AppIcon.vue'
import { toast } from '@/components/ui/toast'
import { messageFor } from '@/composables/useApiError'
import { useClientsStore } from '@/stores/clients'
import { useProjectsStore } from '@/stores/projects'
import { useTasksStore } from '@/stores/tasks'
import { nextProjectColor } from '@/utils/projectColors'

/**
 * Project and its task as one choice, the way Toggl does it: the list starts
 * with projects, and picking one turns the same list into its tasks with a way
 * back. A task cannot exist without a project, so it never has a control of
 * its own.
 *
 * Both values are committed together when the list closes: changing the
 * project and picking its task is one save instead of two writes racing, and a
 * new project never travels with the old task.
 */
const projectId = defineModel<string | null>('projectId', { required: true })
const taskId = defineModel<string | null>('taskId', { required: true })
const props = withDefaults(defineProps<{ compact?: boolean }>(), { compact: false })

const { t } = useI18n()
const projects = useProjectsStore()
const clients = useClientsStore()
const tasks = useTasksStore()

// Never real ids, so they cannot collide with an item.
const NONE = '\u0000none'
const CREATE = '\u0000create'

const open = ref(false)
const query = ref('')
/** Which list is on screen; the chosen project survives a look back. */
const browsing = ref<'projects' | 'tasks'>('projects')
const draftProject = ref<string | null>(null)
const draftTask = ref<string | null>(null)
const creating = ref(false)

const project = computed(() => projects.find(projectId.value))
const task = computed(() => tasks.find(taskId.value))

// The trigger names the task, and the store knows it only once loaded.
watch(
  () => projectId.value,
  (id) => {
    if (!id) return
    void tasks.load(id).catch(() => {
      // Without the list the trigger shows the project alone; nothing breaks.
    })
  },
  { immediate: true },
)

watch(open, (value) => {
  if (value) {
    draftProject.value = projectId.value
    draftTask.value = taskId.value
    browsing.value = projectId.value ? 'tasks' : 'projects'
    void loadTasks(draftProject.value)
    return
  }
  query.value = ''
  if (draftProject.value === projectId.value && draftTask.value === taskId.value) return
  projectId.value = draftProject.value
  taskId.value = draftTask.value
})

function loadTasks(id: string | null): Promise<void> {
  if (!id) return Promise.resolve()
  return tasks.load(id).catch(() => {})
}

/** Archived projects stay selectable only while an entry already points at one. */
const projectItems = computed(() => {
  const current = projects.find(draftProject.value)
  const visible = current?.archived ? [current, ...projects.active] : projects.active
  return visible
    .map((item) => ({
      value: item.id,
      label: item.name,
      color: item.color,
      group: clients.find(item.client_id)?.name,
    }))
    .sort(
      (a, b) => (a.group ?? '').localeCompare(b.group ?? '') || a.label.localeCompare(b.label),
    )
})

const browsingProject = computed(() => projects.find(draftProject.value))
const archivedProject = computed(() => browsingProject.value?.archived === true)

const normalizedQuery = computed(() => query.value.trim().toLocaleLowerCase())

const filteredProjects = computed(() =>
  normalizedQuery.value
    ? projectItems.value.filter((item) => item.label.toLocaleLowerCase().includes(normalizedQuery.value))
    : projectItems.value,
)

const projectSections = computed(() => {
  const ungrouped: typeof filteredProjects.value = []
  const byGroup = new Map<string, typeof filteredProjects.value>()
  for (const item of filteredProjects.value) {
    if (item.group === undefined) ungrouped.push(item)
    else byGroup.set(item.group, [...(byGroup.get(item.group) ?? []), item])
  }
  return [
    { label: undefined, items: ungrouped },
    ...[...byGroup].map(([label, items]) => ({ label, items })),
  ].filter((section) => section.items.length > 0)
})

/** Active tasks of the project; the one already on the entry stays listed
 *  even when it is done, because the server lets it stay there. */
const taskItems = computed(() => {
  const id = draftProject.value
  if (!id) return []
  const selected = tasks.find(draftTask.value)
  const kept = selected?.completed && selected.project_id === id ? [selected] : []
  return [...tasks.sortedOf(id, false), ...kept]
})

const filteredTasks = computed(() =>
  normalizedQuery.value
    ? taskItems.value.filter((item) => item.name.toLocaleLowerCase().includes(normalizedQuery.value))
    : taskItems.value,
)

const showNone = computed(() => !normalizedQuery.value)

const canCreateProject = computed(
  () =>
    normalizedQuery.value !== '' &&
    !projectItems.value.some((item) => item.label.toLocaleLowerCase() === normalizedQuery.value),
)

const canCreateTask = computed(
  () =>
    !archivedProject.value &&
    normalizedQuery.value !== '' &&
    !taskItems.value.some(
      (item) =>
        !item.completed && item.name.toLocaleLowerCase() === normalizedQuery.value,
    ),
)

const selectedValue = computed(() =>
  browsing.value === 'projects' ? (draftProject.value ?? NONE) : (draftTask.value ?? NONE),
)

function choose(value: unknown) {
  if (browsing.value === 'projects') void chooseProject(value)
  else void chooseTask(value)
}

async function chooseProject(value: unknown) {
  if (value === CREATE) {
    await createProject()
    return
  }
  const picked = typeof value === 'string' ? value : NONE
  if (picked === NONE) {
    draftProject.value = null
    draftTask.value = null
    open.value = false
    return
  }
  // A task belongs to its project: a different project drops the old one.
  if (picked !== draftProject.value) draftTask.value = null
  draftProject.value = picked
  browsing.value = 'tasks'
  query.value = ''
  await loadTasks(picked)
}

async function chooseTask(value: unknown) {
  if (value === CREATE) {
    await createTask()
    return
  }
  draftTask.value = typeof value === 'string' && value !== NONE ? value : null
  open.value = false
}

async function createProject() {
  if (creating.value) return
  creating.value = true
  try {
    const color = nextProjectColor(projects.active.map((item) => item.color))
    const created = await projects.create(query.value.trim(), color)
    draftProject.value = created.id
    draftTask.value = null
    browsing.value = 'tasks'
    query.value = ''
  } catch (cause) {
    // The picker stays open on the typed name; a toast says what went wrong.
    toast.error(t('projects.createFailed'), messageFor(cause))
  } finally {
    creating.value = false
  }
}

async function createTask() {
  const id = draftProject.value
  if (!id || creating.value) return
  creating.value = true
  try {
    const created = await tasks.create(id, query.value.trim(), null)
    draftTask.value = created.id
    open.value = false
  } catch (cause) {
    toast.error(t('tasks.createFailed'), messageFor(cause))
  } finally {
    creating.value = false
  }
}

function backToProjects() {
  browsing.value = 'projects'
  query.value = ''
}

const triggerLabel = computed(() => {
  const name = project.value?.name ?? t('timer.noProject')
  return task.value ? `${name}, ${task.value.name}` : name
})
</script>

<template>
  <PopoverRoot v-model:open="open">
    <PopoverTrigger as-child>
      <button
        type="button"
        class="ui-combobox-trigger"
        :aria-label="`${t('timer.projectTask')}: ${triggerLabel}`"
        :title="triggerLabel"
        :data-empty="project ? undefined : ''"
        :data-task="task ? '' : undefined"
        :data-compact="compact ? '' : undefined"
      >
        <span v-if="project" class="ui-combobox-dot" :style="{ background: project.color }" />
        <span class="ui-combobox-value">{{ project?.name ?? t('timer.project') }}</span>
        <span v-if="task" class="ui-combobox-task">· {{ task.name }}</span>
        <!-- A compact chip in a dense row reads as clickable without it. -->
        <AppIcon v-if="!compact" name="chevrons-up-down" :size="14" />
      </button>
    </PopoverTrigger>

    <PopoverPortal>
      <PopoverContent
        class="ui-floating ui-combobox"
        align="start"
        :side-offset="6"
        :collision-padding="8"
      >
        <ListboxRoot
          :model-value="selectedValue"
          selection-behavior="replace"
          highlight-on-hover
          @update:model-value="choose"
        >
          <div v-if="browsing === 'tasks'" class="ui-combobox-head">
            <button
              type="button"
              class="ui-combobox-back"
              :aria-label="t('tasks.backToProjects')"
              :title="t('tasks.backToProjects')"
              @click="backToProjects"
            >
              <AppIcon name="chevron-left" :size="16" />
            </button>
            <span
              class="ui-combobox-dot"
              :style="{ background: browsingProject?.color }"
              aria-hidden="true"
            />
            <span class="ui-combobox-head-project">{{ browsingProject?.name }}</span>
          </div>

          <div class="ui-combobox-search">
            <AppIcon name="search" :size="16" />
            <ListboxFilter
              v-model="query"
              auto-focus
              class="ui-combobox-input"
              :placeholder="t('ui.search')"
              :aria-label="t('ui.search')"
            />
          </div>

          <ListboxContent class="ui-combobox-list">
            <template v-if="browsing === 'projects'">
              <ListboxItem v-if="showNone" :value="NONE" class="ui-menu-item">
                <span class="ui-combobox-dot is-none" />
                <span class="ui-combobox-label muted">{{ t('timer.noProject') }}</span>
                <ListboxItemIndicator class="ui-combobox-check">
                  <AppIcon name="check" :size="16" />
                </ListboxItemIndicator>
              </ListboxItem>

              <ListboxGroup
                v-for="section in projectSections"
                :key="section.label ?? NONE"
                class="ui-combobox-group"
              >
                <ListboxGroupLabel v-if="section.label" class="ui-combobox-group-label">
                  {{ section.label }}
                </ListboxGroupLabel>
                <ListboxItem
                  v-for="item in section.items"
                  :key="item.value"
                  :value="item.value"
                  class="ui-menu-item"
                >
                  <span class="ui-combobox-dot" :style="{ background: item.color }" />
                  <span class="ui-combobox-label">{{ item.label }}</span>
                  <ListboxItemIndicator class="ui-combobox-check">
                    <AppIcon name="check" :size="16" />
                  </ListboxItemIndicator>
                </ListboxItem>
              </ListboxGroup>

              <ListboxItem
                v-if="canCreateProject"
                :value="CREATE"
                class="ui-menu-item ui-combobox-create"
              >
                <AppIcon name="plus" :size="16" />
                <span class="ui-combobox-label">
                  {{ t('ui.create', { name: query.trim() }) }}
                </span>
              </ListboxItem>

              <p
                v-if="!projectSections.length && !canCreateProject && !showNone"
                class="ui-combobox-empty"
              >
                {{ t('ui.noResults') }}
              </p>
            </template>

            <template v-else>
              <ListboxItem v-if="showNone" :value="NONE" class="ui-menu-item">
                <span class="ui-combobox-label muted">{{ t('tasks.none') }}</span>
                <ListboxItemIndicator class="ui-combobox-check">
                  <AppIcon name="check" :size="16" />
                </ListboxItemIndicator>
              </ListboxItem>

              <ListboxItem
                v-for="item in filteredTasks"
                :key="item.id"
                :value="item.id"
                :disabled="archivedProject"
                class="ui-menu-item"
              >
                <span class="ui-combobox-label">{{ item.name }}</span>
                <ListboxItemIndicator class="ui-combobox-check">
                  <AppIcon name="check" :size="16" />
                </ListboxItemIndicator>
              </ListboxItem>

              <ListboxItem
                v-if="canCreateTask"
                :value="CREATE"
                class="ui-menu-item ui-combobox-create"
              >
                <AppIcon name="plus" :size="16" />
                <span class="ui-combobox-label">
                  {{ t('ui.create', { name: query.trim() }) }}
                </span>
              </ListboxItem>

              <p
                v-if="!filteredTasks.length && !canCreateTask && !showNone"
                class="ui-combobox-empty"
              >
                {{ t('ui.noResults') }}
              </p>
              <p v-else-if="!taskItems.length && !canCreateTask" class="ui-combobox-empty">
                {{ archivedProject ? t('tasks.archivedHint') : t('tasks.pickerEmpty') }}
              </p>
            </template>
          </ListboxContent>
        </ListboxRoot>
      </PopoverContent>
    </PopoverPortal>
  </PopoverRoot>
</template>

<style scoped>
/* The project keeps its name and the task gives way: a one-letter project
   tells nothing about the entry. */
.ui-combobox-trigger[data-task] .ui-combobox-value {
  flex: 0 0 auto;
  max-width: 60%;
}
</style>
