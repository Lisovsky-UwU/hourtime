<template>
  <div class="overflow-hidden border-b border-border-dark">
    <div
      class="w-full flex flex-row items-center gap-2 text-left hover:bg-surface px-4 py-2"
    >
      <div class="text-lg font-bold">
        {{ organization.name }}
      </div>
      <div class="bg-surface rounded-lg px-3 border border-background">
        {{ organization.access }}
      </div>

      <div class="flex-grow" />

      <button class="px-3 py-1 cursor-pointer bg-success rounded-lg uppercase">
        {{ $t("message.common.edit") }}
      </button>
      <button class="px-3 py-1 cursor-pointer bg-error rounded-lg uppercase">
        {{ $t("message.common.delete") }}
      </button>
    </div>

    <div class="pl-4 my-1">
      Workspaces
    </div>

    <div>
      <div
        v-for="workspace of organization.workspaces" :key="workspace.id"
        class="pl-8 py-2 hover:bg-surface flex flex-row gap-2 px-4 items-center"
      >
        <div>
          {{ workspace.name }}
        </div>

        <div class="flex-grow" />

        <button class="px-3 py-1 cursor-pointer bg-success rounded-lg uppercase">
          {{ $t("message.common.edit") }}
        </button>
        <button class="px-3 py-1 cursor-pointer bg-error rounded-lg uppercase">
          {{ $t("message.common.delete") }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { type PropType } from 'vue';
import type { OrganizationModel } from '@/stores/models/organization';

const props = defineProps({
  organization: {
    type: Object as PropType<OrganizationModel>,
    required: true,
  },
})
</script>
