<template>
  <div
    ref="selectRef"
    class="px-4 py-2 border rounded-lg focus:outline-none transition-all duration-300
      border-border focus:border-highlight flex flex-row gap-2 cursor-pointer
      hover:bg-bg-light relative"
    @click="toggle"
  >
    <div>
      <div v-if="model.project_id === null" class="text-text-muted">
        {{ $t("message.page.timeEntry.selectProject") }}
      </div>
      <div
        v-else-if="currentTask !== null"
        class="font-bold flex flex-row gap-2"
        :style="{color: currentProject !== null ? currentProject.color : ''}"
      >
        <div>
          # {{ currentTask.number }}
        </div>
        <div>
          {{ currentTask.name }}
        </div>
      </div>
      <div v-else class="font-bold" :style="{color: currentProject.color}">
        {{ currentProject.name }}
      </div>
    </div>

    <transition name="fade">
      <div
        v-if="isOpen"
        ref="itemsRef"
        class="bg-bg absolute top-full z-50 right-0 rounded-lg border border-border py-2
          flex flex-col gap-3 text-text cursor-auto mt-2 w-[350px]"
        @click.stop=""
      >
        <div v-if="model.project_id === null">
          <div
            v-for="project in projects.projects"
            :key="'project_' + project.id"
            class="p-2 font-bold hover:bg-bg-dark cursor-pointer"
            :style="{color: project.color}"
            @click="selectProject(project)"
          >
            {{ project.name }}
          </div>
        </div>
        <div v-else>
          <div class="flex flex-row gap-2 pl-2">
            <svg-icon
              class="hover:bg-bg-light rounded-lg p-1 cursor-pointer"
              type="mdi"
              :path="mdiClose"
              @click="clearProject"
            />
            <div class="font-bold" :style="{color: currentProject.color}">
              {{ currentProject.name }}
            </div>
          </div>
          <div
            v-if="currentTaskList.length === 0"
            class="w-full text-text-muted text-center mt-2"
          >
            {{ $t("message.page.timeEntry.noTaskInProject") }}
          </div>
          <div class="mt-2">
            <div
              v-for="task in currentTaskList"
              :key="task.id"
              class="p-2 hover:bg-bg-dark flex flex-row gap-2 cursor-pointer"
              :class="{'bg-bg-light': currentTask !== null && currentTask.id === task.id}"
              @click="selectTask(task)"
            >
              <div>
                # {{ task.number }}
              </div>
              <div>
                {{ task.name }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
import SvgIcon from '@jamescoyle/vue-icon'
import { mdiClose } from '@mdi/js';
import { useProjects } from '@/stores/projects';
import { useTasks } from '@/stores/tasks';
import type { TimeEntryModel } from '@/stores/models/time-entry';
import type { ProjectModel } from '@/stores/models/project';
import type { TaskModel } from '@/stores/models/task';

const model = defineModel<TimeEntryModel>({required: true})

const projects = useProjects()
const tasks = useTasks()

const emit = defineEmits(['update'])

const selectRef = ref(null)
const itemsRef = ref(null)
const isOpen = ref(false)

function selectProject(project: ProjectModel) {
  model.value.project_id = project.id
  emit("update", model)
}

function clearProject() {
  model.value.project_id = null
  model.value.task_id = null
  emit("update", model)
}

function selectTask(task: TaskModel) {
  if (model.value.task_id === task.id) {
    model.value.task_id = null
  } else {
    model.value.task_id = task.id
  }
  emit("update", model)
}

const toggle = () => {
  isOpen.value ? close() : open()
}

const open = async () => {
  isOpen.value = true
  await nextTick()
}

const close = () => {
  isOpen.value = false
}

const handleClickOutside = (event: MouseEvent) => {
  if (selectRef.value && !selectRef.value.contains(event.target)) {
    close()
  }
}

const currentProject = computed<ProjectModel>(() => projects.projectsMap[model.value.project_id])
const currentTaskList = computed<TaskModel[]>(
  () => currentProject === undefined ? [] : tasks.tasksMapByProjects[currentProject.value.id]
)

const currentTask = computed<TaskModel | null>(
  () => model.value.task_id !== null ? tasks.tasksMap[model.value.task_id] : null
)

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>
