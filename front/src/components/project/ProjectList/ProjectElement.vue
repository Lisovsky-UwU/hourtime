<template>
  <div
    class="w-full flex flex-row items-center gap-2 text-left px-4 py-2 hover:bg-bg-dark"
  >
    <div class="text-lg font-bold" :style="{color: project.color}">
      {{ project.name }}
    </div>

    <div class="flex-grow" />

    <button class="circle-button hover-button-edit" @click="emit('editProject', project)">
      <svg-icon size="24" type="mdi" :path="mdiPen" />
    </button>
    <button class="circle-button hover-button-delete" @click="emit('deleteProject', project)">
      <svg-icon size="24" type="mdi" :path="mdiDelete" />
    </button>
  </div>
</template>

<script setup lang="ts">
import SvgIcon from '@jamescoyle/vue-icon'
import { mdiPen, mdiDelete } from '@mdi/js'
import type { ProjectModel } from '@/stores/models/project';
import type { PropType } from 'vue';

const emit = defineEmits(["editProject", "deleteProject"])

defineProps({
  project: {
    type: Object as PropType<ProjectModel>,
    required: true,
  }
})
</script>

<style scoped>
@import 'tailwindcss';
@import '@/assets/theme.css';

.hover-button-edit {
  @apply hover:bg-bg-light;
}

.hover-button-delete {
  @apply hover:bg-danger;
}
</style>

