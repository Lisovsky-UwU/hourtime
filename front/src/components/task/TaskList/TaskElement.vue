<template>
  <div
    class="w-full flex flex-row items-center gap-2 text-left px-4 py-2 hover:bg-bg-dark"
  >
    <div class="text-lg font-bold">
      {{ task.name }}
    </div>

    <div class="flex-grow" />

    <button class="circle-button hover-button">
      <svg-icon size="24" type="mdi" :path="mdiPen" />
    </button>
    <button class="circle-button hover-button">
      <svg-icon size="24" type="mdi" :path="mdiDelete" />
    </button>
  </div>
</template>

<script setup lang="ts">
import type { PropType } from 'vue';
import SvgIcon from '@jamescoyle/vue-icon'
import { mdiPen, mdiDelete } from '@mdi/js'
import type { TaskModel } from '@/stores/models/task';

defineProps({
  task: {
    type: Object as PropType<TaskModel>,
    required: true,
  }
})
</script>

<style scoped>
@import 'tailwindcss';
@import '@/assets/theme.css';

.hover-button {
  @apply hover:bg-bg-light;
}
</style>

