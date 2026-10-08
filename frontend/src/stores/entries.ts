import { ref } from 'vue'
import { defineStore } from 'pinia'

import * as entriesApi from '@/api/timeEntries'
import type { EntryPatch, ListQuery } from '@/api/timeEntries'
import type { TimeEntry } from '@/types'

const PAGE_SIZE = 50

export const useEntriesStore = defineStore('entries', () => {
  const items = ref<TimeEntry[]>([])
  const hasMore = ref(false)
  const loading = ref(false)
  const projectFilter = ref<string | null>(null)

  /** A reload already on the wire; concurrent callers wait on it instead of
   *  firing their own. Focus and visibilitychange love to arrive together. */
  let inFlight: Promise<void> | null = null

  function query(offset: number): ListQuery {
    return {
      limit: PAGE_SIZE,
      offset,
      ...(projectFilter.value ? { project_id: projectFilter.value } : {}),
    }
  }

  function newestFirst(list: TimeEntry[]): TimeEntry[] {
    return [...list].sort((a, b) => Date.parse(b.started_at) - Date.parse(a.started_at))
  }

  function load(): Promise<void> {
    if (inFlight) return inFlight

    loading.value = true
    inFlight = entriesApi
      .list(query(0))
      .then((page) => {
        items.value = page.items
        hasMore.value = page.has_more
      })
      .finally(() => {
        loading.value = false
        inFlight = null
      })
    return inFlight
  }

  async function loadMore(): Promise<void> {
    if (loading.value || !hasMore.value) return
    loading.value = true
    try {
      const page = await entriesApi.list(query(items.value.length))
      items.value = newestFirst([...items.value, ...page.items])
      hasMore.value = page.has_more
    } finally {
      loading.value = false
    }
  }

  /**
   * Fold one entry into the list without a round trip.
   *
   * Every write already returns the saved entry, so starting, stopping or
   * editing a timer costs one request instead of two.
   */
  function upsert(entry: TimeEntry): void {
    const others = items.value.filter((item) => item.id !== entry.id)
    // A filtered list must not gain rows that fall outside the filter.
    if (projectFilter.value && entry.project_id !== projectFilter.value) {
      items.value = others
      return
    }
    items.value = newestFirst([...others, entry])
  }

  async function update(id: string, patch: EntryPatch): Promise<TimeEntry> {
    const updated = await entriesApi.update(id, patch)
    upsert(updated)
    return updated
  }

  async function create(payload: Parameters<typeof entriesApi.create>[0]): Promise<TimeEntry> {
    const created = await entriesApi.create(payload)
    upsert(created)
    return created
  }

  async function remove(id: string): Promise<void> {
    await entriesApi.remove(id)
    items.value = items.value.filter((entry) => entry.id !== id)
  }

  async function setProjectFilter(projectId: string | null): Promise<void> {
    projectFilter.value = projectId
    await load()
  }

  function reset(): void {
    items.value = []
    hasMore.value = false
    projectFilter.value = null
  }

  return {
    items,
    hasMore,
    loading,
    projectFilter,
    load,
    loadMore,
    upsert,
    update,
    create,
    remove,
    setProjectFilter,
    reset,
  }
})
