<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import * as workspacesApi from '@/api/workspaces'
import AppIcon from '@/components/AppIcon.vue'
import NameDialog from '@/components/NameDialog.vue'
import type { MenuEntry } from '@/components/ui/UiDropdownMenu.vue'
import UiDropdownMenu from '@/components/ui/UiDropdownMenu.vue'
import { toast } from '@/components/ui/toast'
import { messageFor } from '@/composables/useApiError'
import { useAuthStore } from '@/stores/auth'
import { useWorkspaceStore } from '@/stores/workspace'
import type { Workspace } from '@/types'

defineProps<{ compact?: boolean }>()

const { t } = useI18n()
const auth = useAuthStore()
const workspace = useWorkspaceStore()

const workspaces = ref<Workspace[]>([])
const creating = ref(false)

/**
 * The profile remembers the choice for the next load and new tabs; a full load
 * is the simplest way to drop every list kept for the old workspace.
 */
async function open(id: string) {
  await auth.updateProfile({ default_workspace_id: id })
  window.location.assign('/timer')
}

function switchTo(id: string) {
  if (id === workspace.item?.id) return
  open(id).catch((cause: unknown) => toast.error(messageFor(cause)))
}

async function create(name: string) {
  const created = await workspacesApi.create(name)
  await open(created.id)
}

const items = computed<MenuEntry[]>(() => [
  ...workspaces.value.map((item) => ({
    label: item.name,
    icon: item.id === workspace.item?.id ? ('check' as const) : undefined,
    select: () => switchTo(item.id),
  })),
  'separator',
  { label: t('workspaces.create'), icon: 'plus', select: () => (creating.value = true) },
])

onMounted(() => {
  void workspace.load().catch(() => {})
  workspacesApi
    .list()
    .then((found) => (workspaces.value = found))
    .catch(() => {})
})
</script>

<template>
  <UiDropdownMenu :items="items" :label="t('workspaces.switch')" align="start">
    <template #trigger>
      <button type="button" class="switcher" :aria-label="t('workspaces.switch')">
        <span v-if="!compact" class="switcher-name">{{ workspace.item?.name ?? '' }}</span>
        <AppIcon name="chevrons-up-down" :size="16" />
      </button>
    </template>
  </UiDropdownMenu>

  <NameDialog
    :open="creating"
    :title="t('workspaces.createTitle')"
    :label="t('workspaces.name')"
    :placeholder="t('workspaces.namePlaceholder')"
    initial=""
    :submit-label="t('workspaces.create')"
    :save="create"
    @close="creating = false"
  />
</template>

<style scoped>
.switcher {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  width: 100%;
  height: var(--control-h);
  padding: 0 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: none;
  color: var(--text);
  font: inherit;
  font-weight: 500;
  cursor: pointer;
}

.switcher:hover {
  background: var(--surface-muted);
}

.switcher-name {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
