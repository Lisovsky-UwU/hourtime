import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import * as entriesApi from '@/api/timeEntries'
import type { EntryPatch } from '@/api/timeEntries'
import type { TimeEntry } from '@/types'

const PAGE_SIZE = 50

export const useEntriesStore = defineStore('entries', () => {
  const items = ref<TimeEntry[]>([])
  const total = ref(0)
  const loading = ref(false)
  const projectFilter = ref<string | null>(null)

  const hasMore = computed(() => items.value.length < total.value)

  async function load(): Promise<void> {
    loading.value = true
    try {
      const page = await entriesApi.list({
        limit: PAGE_SIZE,
        offset: 0,
        ...(projectFilter.value ? { project_id: projectFilter.value } : {}),
      })
      items.value = page.items
      total.value = page.total
    } finally {
      loading.value = false
    }
  }

  async function loadMore(): Promise<void> {
    if (loading.value || !hasMore.value) return
    loading.value = true
    try {
      const page = await entriesApi.list({
        limit: PAGE_SIZE,
        offset: items.value.length,
        ...(projectFilter.value ? { project_id: projectFilter.value } : {}),
      })
      items.value = [...items.value, ...page.items]
      total.value = page.total
    } finally {
      loading.value = false
    }
  }

  async function update(id: string, patch: EntryPatch): Promise<TimeEntry> {
    const updated = await entriesApi.update(id, patch)
    // Editing the start time can change the order, so re-sort rather than
    // patching in place.
    items.value = items.value
      .map((entry) => (entry.id === id ? updated : entry))
      .sort((a, b) => Date.parse(b.started_at) - Date.parse(a.started_at))
    return updated
  }

  async function create(payload: {
    started_at: string
    stopped_at: string
    project_id?: string | null
    description?: string
  }): Promise<TimeEntry> {
    const created = await entriesApi.create(payload)
    await load()
    return created
  }

  async function remove(id: string): Promise<void> {
    await entriesApi.remove(id)
    items.value = items.value.filter((entry) => entry.id !== id)
    total.value = Math.max(0, total.value - 1)
  }

  async function setProjectFilter(projectId: string | null): Promise<void> {
    projectFilter.value = projectId
    await load()
  }

  function reset(): void {
    items.value = []
    total.value = 0
    projectFilter.value = null
  }

  return {
    items,
    total,
    loading,
    projectFilter,
    hasMore,
    load,
    loadMore,
    update,
    create,
    remove,
    setProjectFilter,
    reset,
  }
})
