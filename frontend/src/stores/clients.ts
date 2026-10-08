import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import * as clientsApi from '@/api/clients'
import type { ClientPatch } from '@/api/clients'
import type { Client } from '@/types'

export const useClientsStore = defineStore('clients', () => {
  const items = ref<Client[]>([])
  const loading = ref(false)
  const loaded = ref(false)

  const active = computed(() => items.value.filter((client) => !client.archived))
  const byId = computed(() => new Map(items.value.map((client) => [client.id, client])))

  function find(id: string | null): Client | undefined {
    return id ? byId.value.get(id) : undefined
  }

  async function load(force = false): Promise<void> {
    if (loaded.value && !force) return
    loading.value = true
    try {
      // Archived ones too: projects may still point at them.
      items.value = await clientsApi.list(true)
      loaded.value = true
    } finally {
      loading.value = false
    }
  }

  async function create(name: string): Promise<Client> {
    const client = await clientsApi.create(name)
    items.value = [...items.value, client]
    return client
  }

  async function update(id: string, patch: ClientPatch): Promise<Client> {
    const updated = await clientsApi.update(id, patch)
    items.value = items.value.map((client) => (client.id === id ? updated : client))
    return updated
  }

  async function remove(id: string): Promise<void> {
    await clientsApi.remove(id)
    items.value = items.value.filter((client) => client.id !== id)
  }

  function reset(): void {
    items.value = []
    loaded.value = false
  }

  return { items, loading, loaded, active, byId, find, load, create, update, remove, reset }
})
