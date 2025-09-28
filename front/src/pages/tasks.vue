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
        @click="createTask"
      >
        {{ $t("message.common.create") }}
      </Button>
    </div>
  </div>

  <div v-if="loading" class="w-full justify-center flex items-center">
    <Loader />
  </div>

  <div v-else>
    <div
      v-if="tasks.tasks?.length === 0"
      class="w-full text-center mt-3 text-2xl text-text-muted"
    >
      {{ $t("message.page.task.noTasks") }}
    </div>
    <TaskList :tasks="tasks.tasks" v-else />
  </div>

  <dialog id="pop-up">Привет, я поп-ап!</dialog>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';
import Button from '@/components/ui/Button.vue';
import TaskList from '@/components/task/TaskList/index.vue'
import Loader from '@/components/ui/Loader.vue';
import { useTasks } from '@/stores/tasks';

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

function createTask() {
  document.getElementById('pop-up').showModal()
}
</script>

