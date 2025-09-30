<template>
  <div>
    <div class="flex p-3">
      <div class="text-2xl">
        {{ $t("message.page.task.title") }}
      </div>
      <div class="flex-grow"/>
      <Button
        second
        class=""
        :disabled="loading"
        @click="doCreateTask"
      >
        <svg-icon type="mdi" :path="mdiPlus" />
        {{ $t("message.common.create") }}
      </Button>
    </div>
  </div>

  <div v-if="loading" class="w-full justify-center flex items-center">
    <Loader />
  </div>

  <div v-else>
    <div
      v-if="tasks.tasks?.length === 0 || tasks.tasks === null"
      class="w-full text-center mt-3 text-2xl text-text-muted"
    >
      {{ $t("message.page.task.noTasks") }}
    </div>
    <TaskList
      :tasks="tasks.tasks"
      v-else
      @edit-task="doEditTask"
      @delete-task="doDeleteTask"
    />
  </div>

  <Dialog v-if="currentEditTask.taskData !== null" v-model="showEditDialog">
    <div class="flex flex-col gap-4 min-w-[550px]">
      <EditTask
        v-model="currentEditTask.taskData"
        @updated="showEditDialog = false"
      />
      <Button
        block
        @click="showEditDialog = false"
      >
        {{ $t("message.common.cancel") }}
      </Button>
    </div>
  </Dialog>

  <Dialog v-model="showDeleteDialog">
    <div class="flex flex-col gap-4">
      <div class="text-xl">
        {{ $t("message.page.task.confirmDelete") }}
      </div>

      <div class="p-4 rounded-lg bg-bg-light flex flex-col">
        #{{ currentEditTask.taskData?.number }} {{ currentEditTask.taskData?.name }}
      </div>

      <Button
        block
        color="danger"
        :loading="deleteLoading"
        @click="deleteTask"
      >
        {{ $t("message.common.delete") }}
      </Button>
      <Button
        block
        :disabled="deleteLoading"
        @click="showDeleteDialog = false"
      >
        {{ $t("message.common.cancel") }}
      </Button>
    </div>

  </Dialog>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue';
import Button from '@/components/ui/Button.vue';
import TaskList from '@/components/task/TaskList/index.vue'
import Dialog from '@/components/ui/Dialog.vue';
import EditTask from '@/components/task/EditTask.vue';
import Loader from '@/components/ui/Loader.vue';
import { useTasks } from '@/stores/tasks';
import SvgIcon from '@jamescoyle/vue-icon'
import { mdiPlus } from '@mdi/js';
import type { TaskModel } from '@/stores/models/task';

const tasks = useTasks()
const loading = ref(true)

onMounted(async () => {
  if (tasks.tasks === null) {
    await tasks.loadTasks()
  }
  loading.value = false
})

watch(
  () => tasks.tasks,
  (newValue) => {
    loading.value = newValue === null
  }
)

const showEditDialog = ref(false)
const showDeleteDialog = ref(false)
const currentEditTask = reactive({
  taskData: null as null | any,
})

const deleteLoading = ref(false)

function doCreateTask() {
  currentEditTask.taskData = {
    id: null,
    number: null,
    name: "",
    description: null,
    project_id: null,
  }
  showEditDialog.value = true
}

function doEditTask(task: TaskModel) {
  currentEditTask.taskData = {
    id: task.id,
    number: task.number,
    name: task.name,
    description: task.description,
    project_id: task.project_id,
  }
  showEditDialog.value = true
}

function doDeleteTask(task: TaskModel) {
  currentEditTask.taskData = task
  showDeleteDialog.value = true
}

async function deleteTask() {
  if (currentEditTask.taskData !== null) {
    deleteLoading.value = true
    try {
      await tasks.deleteTask(currentEditTask.taskData.id)
      showDeleteDialog.value = false
    } finally {
      deleteLoading.value = false
    }
  }
}

</script>

