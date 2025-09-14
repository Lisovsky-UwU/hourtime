<template>
  <div
    ref="selectRef"
    class="custom-select"
    :class="{ open: isOpen }"
    @click="toggle"
  >
    <div class="select-selected" :class="{active: isOpen}">
      {{ organizations.currentOrganization?.name }} &ndash; {{ workspaces.selectedWorkspace?.name }}
    </div>

    <transition name="fade">
      <div v-show="isOpen" class="select-items" ref="itemsRef" @click.stop="">
        <div
          v-for="(organization, org_index) in organizations.organizations"
          class="organization"
          :key="org_index"
        >
          <div class="organization-name">
            {{ organization.name }}
          </div>
          <div
            v-for="(workspace, ws_index) in organization.workspaces"
            :key="ws_index"
            class="workspace"
            :class="{ active: workspace.id === workspaces.selectedWorkspace?.id }"
            @click.stop="selectItem(organization, workspace)"
          >
            {{ workspace.name }}
          </div>
        </div>
        <button
          class="w-full uppercase bg-border-primary cursor-pointer py-1 px-1
          hover:bg-border-primary-hover transition-all relative flex items-center"
          to="/organizations"
          @click="router.push('/organizations'); close()"
        >
          <svg-icon type="mdi" :path="mdiCogs" />
          <div class="absolute left-1/2 transform -translate-x-1/2">
          {{ $t("message.common.manage") }}
          </div>
        </button>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import router from '@/router';
import SvgIcon from '@jamescoyle/vue-icon'
import { mdiCogs } from '@mdi/js';
import { useOrganizations } from '@/stores/organizations';
import { useWorkspaces } from '@/stores/workspaces';
import type { OrganizationModel } from '@/stores/models/organization';
import type { WorkspaceModel } from '@/stores/models/workspace';

const organizations = useOrganizations()
const workspaces = useWorkspaces()

const emit = defineEmits(['update:modelValue', 'change'])

const selectRef = ref(null)
const itemsRef = ref(null)
const isOpen = ref(false)

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

const selectItem = (organization: OrganizationModel, workspace: WorkspaceModel) => {
  if (workspace.id !== workspaces.currentWorkspace?.id) {
    organizations.selectOrganization(organization, workspace)
    emit('change')
  }
  close()
}

const handleClickOutside = (event: MouseEvent) => {
  if (selectRef.value && !selectRef.value.contains(event.target)) {
    close()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
@import 'tailwindcss';
@import '@/assets/theme.css';

.custom-select {
  @apply relative w-auto;
}

.select-selected {
  @apply w-[300px] py-2 px-6 bg-background rounded-lg items-center select-none cursor-pointer
  border-t-[2px] border-x-[2px] border-background transition-all overflow-hidden whitespace-nowrap
  text-ellipsis transition-all;
}

.select-selected:hover, .select-selected.active {
  @apply bg-background-hover;
}

.custom-select.open .select-selected {
  @apply rounded-b-none rounded-t-lg border-border-primary;
}

.select-items {
  scrollbar-color: var(--color-surface) var(--color-background);
  scrollbar-width: thin;
  @apply bg-background absolute top-full z-50 left-0 right-0 max-h-[350px] overflow-y-auto
  rounded-b-lg border-x-[2px] border-b-[2px] border-border-primary;
}

.organization {
  @apply border-t-[2px] border-border-primary;
}

.organization-name {
  @apply p-2 font-bold;
}

.workspace {
  @apply px-5 py-2 flex items-center cursor-pointer;
}

.workspace:hover {
  @apply bg-background-hover;
}
.workspace.active {
  @apply bg-surface;
}

.organization:first-child {
  @apply border-none;
}

/* Анимация появления */
.fade-enter-active,
.fade-leave-active {
  @apply transition-opacity;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
