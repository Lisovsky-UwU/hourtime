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

      <button
        class="rounded-lg uppercase py-1 px-3 hover:bg-bg-light transition-all
        flex flex-row gap-3"
        @click="emit('addWorkspace', organization)"
      >
        <svg-icon type="mdi" :path="mdiPlus" />
        {{ $t("message.page.organization.addWorkspace") }}
      </button>
      <button
        class="circle-button hover-button-edit"
        @click="emit('editOrganization', organization)"
        :title="$t('message.page.organization.edit')"
      >
        <svg-icon size="24" type="mdi" :path="mdiPen" />
      </button>
      <button
        class="circle-button hover-button-delete"
        @click="emit('deleteOrganization', organization)"
        :title="$t('message.page.organization.delete')"
      >
        <svg-icon size="24" type="mdi" :path="mdiDelete" />
      </button>
    </div>

    <div class="pl-4 my-1 flex flex-row">
      <div>
        {{ $t("message.page.organization.workspaces")}}
      </div>
      <div class="flex-grow" />
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

        <button
          class="circle-button hover-button-edit"
          :title="$t('message.page.organization.editWorkspace')"
          @click="emit('editWorkspace', workspace, organization)"
        >
          <svg-icon size="24" type="mdi" :path="mdiPen" />
        </button>
        <button
          class="circle-button hover-button-delete"
          :title="$t('message.page.organization.deleteWorkspace')"
          @click="emit('deleteWorkspace', workspace, organization)"
        >
          <svg-icon size="24" type="mdi" :path="mdiDelete" />
        </button>
      </div>
    </div>
  </div>


</template>

<script setup lang="ts">
import { type PropType } from 'vue';
import SvgIcon from '@jamescoyle/vue-icon'
import { mdiPen, mdiDelete, mdiPlus } from '@mdi/js'
import type { OrganizationModel } from '@/stores/models/organization';

defineProps({
  organization: {
    type: Object as PropType<OrganizationModel>,
    required: true,
  },
})

const emit = defineEmits([
  "editOrganization",
  "deleteOrganization",
  "addWorkspace",
  "editWorkspace",
  "deleteWorkspace",
])
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
