import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import * as projectsApi from '@/api/projects'
import type { ProjectPatch } from '@/api/projects'
import type { Project } from '@/types'

export const useProjectsStore = defineStore('projects', () => {
  const items = ref<Project[]>([])
  const loading = ref(false)
  const loaded = ref(false)
  const includeArchived = ref(false)

  const active = computed(() => items.value.filter((project) => !project.archived))
  const byId = computed(() => new Map(items.value.map((project) => [project.id, project])))

  function find(id: string | null): Project | undefined {
    return id ? byId.value.get(id) : undefined
  }

  async function load(force = false): Promise<void> {
    if (loaded.value && !force) return
    loading.value = true
    try {
      // Always fetch archived ones too: entries may still point at them.
      items.value = await projectsApi.list(true)
      loaded.value = true
    } finally {
      loading.value = false
    }
  }

  async function create(name: string, color: string): Promise<Project> {
    const project = await projectsApi.create(name, color)
    items.value = [...items.value, project]
    return project
  }

  async function update(id: string, patch: ProjectPatch): Promise<Project> {
    const updated = await projectsApi.update(id, patch)
    items.value = items.value.map((project) => (project.id === id ? updated : project))
    return updated
  }

  async function remove(id: string): Promise<void> {
    await projectsApi.remove(id)
    items.value = items.value.filter((project) => project.id !== id)
  }

  function reset(): void {
    items.value = []
    loaded.value = false
  }

  return {
    items,
    loading,
    loaded,
    includeArchived,
    active,
    byId,
    find,
    load,
    create,
    update,
    remove,
    reset,
  }
})
