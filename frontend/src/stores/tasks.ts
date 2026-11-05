import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import * as tasksApi from '@/api/tasks'
import type { TaskPatch } from '@/api/tasks'
import type { Task } from '@/types'

/**
 * Tasks of every project loaded in this session, active and completed alike.
 * Pages and pickers filter locally, so switching back to a project costs no
 * request; `load` refreshes one project at a time.
 */
export const useTasksStore = defineStore('tasks', () => {
  const items = ref<Task[]>([])
  const loading = ref(false)
  const loadedProjects = ref<string[]>([])

  /** One request per project: a list of rows all asks for the same tasks at once. */
  const inFlight = new Map<string, Promise<void>>()

  const byId = computed(() => new Map(items.value.map((task) => [task.id, task])))

  function find(id: string | null): Task | undefined {
    return id ? byId.value.get(id) : undefined
  }

  /** Alphabetical, so a list of tasks reads like the rest of the app. */
  function sortedOf(projectId: string, completed: boolean): Task[] {
    return items.value
      .filter((task) => task.project_id === projectId && task.completed === completed)
      .sort((a, b) => a.name.localeCompare(b.name))
  }

  function loaded(projectId: string): boolean {
    return loadedProjects.value.includes(projectId)
  }

  function load(projectId: string, force = false): Promise<void> {
    if (!force) {
      const running = inFlight.get(projectId)
      if (running) return running
      if (loaded(projectId)) return Promise.resolve()
    }
    loading.value = true
    const request = tasksApi
      .list(projectId, true)
      .then((found) => {
        items.value = [...items.value.filter((task) => task.project_id !== projectId), ...found]
        loadedProjects.value = [...new Set([...loadedProjects.value, projectId])]
      })
      .finally(() => {
        loading.value = false
        inFlight.delete(projectId)
      })
    inFlight.set(projectId, request)
    return request
  }

  async function create(
    projectId: string,
    name: string,
    estimatedSeconds: number | null,
  ): Promise<Task> {
    const task = await tasksApi.create(projectId, name, estimatedSeconds)
    items.value = [...items.value, task]
    return task
  }

  async function update(id: string, patch: TaskPatch): Promise<Task> {
    const updated = await tasksApi.update(id, patch)
    items.value = items.value.map((task) => (task.id === id ? updated : task))
    return updated
  }

  async function setCompleted(id: string, completed: boolean): Promise<Task> {
    const updated = await tasksApi.setCompleted(id, completed)
    items.value = items.value.map((task) => (task.id === id ? updated : task))
    return updated
  }

  async function remove(id: string): Promise<void> {
    await tasksApi.remove(id)
    items.value = items.value.filter((task) => task.id !== id)
  }

  function reset(): void {
    items.value = []
    loadedProjects.value = []
    inFlight.clear()
  }

  return {
    items,
    loading,
    byId,
    find,
    sortedOf,
    loaded,
    load,
    create,
    update,
    setCompleted,
    remove,
    reset,
  }
})
