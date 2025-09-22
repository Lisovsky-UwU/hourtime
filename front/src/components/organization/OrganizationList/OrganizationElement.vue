<template>
  <div class="overflow-hidden border-b border-border">
    <div
      class="w-full flex flex-row items-center gap-2 text-left px-4 py-2 hover:bg-bg-dark"
    >
      <div class="text-lg font-bold">
        {{ organization.name }}
      </div>
      <div class="bg-bg-light rounded-lg px-3 border border-border">
        {{ organization.access }}
      </div>

      <div class="flex-grow" />

      <button class="circle-button hover-buttons">
        <svg-icon size="24" type="mdi" :path="mdiPen" />
      </button>
      <button class="circle-button hover-buttons">
        <svg-icon size="24" type="mdi" :path="mdiDelete" />
      </button>
    </div>

    <div class="pl-4 my-1">
      Workspaces
    </div>

    <div>
      <div
        v-for="workspace of organization.workspaces" :key="workspace.id"
        class="pl-8 py-2 flex flex-row gap-2 px-4 items-center hover:bg-bg-dark"
      >
        <div>
          {{ workspace.name }}
        </div>

        <div class="flex-grow" />

        <button class="circle-button hover-buttons">
          <svg-icon size="24" type="mdi" :path="mdiPen" />
        </button>
        <button class="circle-button hover-buttons">
          <svg-icon size="24" type="mdi" :path="mdiDelete" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { type PropType } from 'vue';
import SvgIcon from '@jamescoyle/vue-icon'
import { mdiPen, mdiDelete } from '@mdi/js'
import type { OrganizationModel } from '@/stores/models/organization';

const props = defineProps({
  organization: {
    type: Object as PropType<OrganizationModel>,
    required: true,
  },
})
</script>

<style scoped>
@import 'tailwindcss';
@import '@/assets/theme.css';

.hover-buttons {
  @apply hover:bg-bg-light;
}
</style>
