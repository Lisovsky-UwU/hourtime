import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import * as tagsApi from '@/api/tags'
import type { Tag } from '@/types'

export const useTagsStore = defineStore('tags', () => {
  const items = ref<Tag[]>([])
  const loading = ref(false)
  const loaded = ref(false)

  const sorted = computed(() => [...items.value].sort((a, b) => a.name.localeCompare(b.name)))
  const byId = computed(() => new Map(items.value.map((tag) => [tag.id, tag])))

  /** Names of the tags that still exist, alphabetically; ids of deleted ones are skipped. */
  function namesOf(ids: readonly string[]): string[] {
    return ids
      .map((id) => byId.value.get(id)?.name)
      .filter((name): name is string => name !== undefined)
      .sort((a, b) => a.localeCompare(b))
  }

  async function load(force = false): Promise<void> {
    if (loaded.value && !force) return
    loading.value = true
    try {
      items.value = await tagsApi.list()
      loaded.value = true
    } finally {
      loading.value = false
    }
  }

  async function create(name: string): Promise<Tag> {
    const tag = await tagsApi.create(name)
    items.value = [...items.value, tag]
    return tag
  }

  async function rename(id: string, name: string): Promise<Tag> {
    const updated = await tagsApi.rename(id, name)
    items.value = items.value.map((tag) => (tag.id === id ? updated : tag))
    return updated
  }

  async function remove(id: string): Promise<void> {
    await tagsApi.remove(id)
    items.value = items.value.filter((tag) => tag.id !== id)
  }

  function reset(): void {
    items.value = []
    loaded.value = false
  }

  return { items, loading, loaded, sorted, byId, namesOf, load, create, rename, remove, reset }
})
