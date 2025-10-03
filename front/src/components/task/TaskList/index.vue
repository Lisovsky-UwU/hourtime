<template>
  <table class="w-full">
    <thead>
      <tr>
        <th scope="col" class="px-10 w-[1%]">{{ $t("message.page.task.colId") }}</th>
        <th scope="col">{{ $t("message.page.task.colName") }}</th>
        <th scope="col">{{ $t("message.page.task.colProject") }}</th>
        <th scope="col" class="px-10 w-[1%]">{{ $t("message.page.task.colActions") }}</th>
      </tr>
    </thead>

    <tbody>
      <tr
        v-for="task in tasks"
        :key="task.id"
        class="hover:bg-bg-dark"
      >
        <td class="text-center">{{ task.number }}</td>
        <td>{{ task.name }}</td>
        <td v-if="task.project_id === null">-</td>
        <td v-else-if="projects.projectsMap === null">
          <Loader type="circle" class="w-[20px] h-[20px]"/>
        </td>
        <td v-else class="font-bold" :style="{color: projects.projectsMap[task.project_id].color}">
          {{projects.projectsMap[task.project_id].name}}
        </td>

        <td>
          <div class="flex justify-center gap-2">
            <button class="circle-button hover-button-edit" @click="emit('editTask', task)">
              <svg-icon size="24" type="mdi" :path="mdiPen" />
            </button>
            <button class="circle-button hover-button-delete" @click="emit('deleteTask', task)">
              <svg-icon size="24" type="mdi" :path="mdiDelete" />
            </button>
          </div>
        </td>
      </tr>
    </tbody>
  </table>
</template>

<script setup lang="ts">
import SvgIcon from '@jamescoyle/vue-icon'
import { mdiPen, mdiDelete } from '@mdi/js'
import type { PropType } from 'vue';
import type { TaskModel } from '@/stores/models/task';
import { useProjects } from '@/stores/projects';
import Loader from '@/components/ui/Loader.vue';

defineProps({
  tasks: {
    type: Array as PropType<TaskModel[]>,
    required: true
  }
})

const emit = defineEmits(["editTask", "deleteTask"])

const projects = useProjects()
</script>

<style scoped>
@import 'tailwindcss';
@import '@/assets/theme.css';

th {
  @apply py-2 font-normal text-lg text-left border-b border-border;
}

td {
  @apply py-2 text-lg border-b border-border;
}

.hover-button-edit {
  @apply hover:bg-bg-light;
}

.hover-button-delete {
  @apply hover:bg-danger;
}
</style>
