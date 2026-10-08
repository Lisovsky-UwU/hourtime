import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import * as workspacesApi from '@/api/workspaces'
import type { Workspace, WorkspacePatch } from '@/types'
import { toCents } from '@/utils/money'

/** Billing settings of the current workspace: the default rate and the currency. */
export const useWorkspaceStore = defineStore('workspace', () => {
  const item = ref<Workspace | null>(null)
  const loaded = ref(false)

  /** USD until loaded - the server default, so a first paint rarely changes. */
  const currency = computed(() => item.value?.currency ?? 'USD')
  const defaultRateCents = computed(() => toCents(item.value?.default_hourly_rate ?? null))

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

  return { item, loaded, currency, defaultRateCents, load, update, reset }
})
