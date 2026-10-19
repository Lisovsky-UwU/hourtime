import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import * as workspacesApi from '@/api/workspaces'
import type { Workspace, WorkspacePatch } from '@/types'
import { toCents } from '@/utils/money'

/** The current workspace: billing settings and the caller's role in it. */
export const useWorkspaceStore = defineStore('workspace', () => {
  const item = ref<Workspace | null>(null)
  const loaded = ref(false)

  /** USD until loaded - the server default, so a first paint rarely changes. */
  const currency = computed(() => item.value?.currency ?? 'USD')
  const defaultRateCents = computed(() => toCents(item.value?.default_hourly_rate ?? null))
  /**
   * Edit and delete controls. True until loaded: most workspaces are personal,
   * so admins see no flicker, and the server refuses a member anyway.
   */
  const canManage = computed(() => item.value?.role !== 'member')

  async function load(force = false): Promise<void> {
    if (loaded.value && !force) return
    item.value = await workspacesApi.current()
    loaded.value = true
  }

  async function update(patch: WorkspacePatch): Promise<Workspace> {
    item.value = await workspacesApi.updateCurrent(patch)
    return item.value
  }

  function reset(): void {
    item.value = null
    loaded.value = false
  }

  return { item, loaded, currency, defaultRateCents, canManage, load, update, reset }
})
