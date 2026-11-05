import { inWorkspace, request } from '@/api/client'
import type { Task } from '@/types'

/** All tasks of one project, completed ones included unless asked otherwise. */
export function list(projectId: string, includeCompleted = true): Promise<Task[]> {
  return request<Task[]>(inWorkspace('/tasks'), {
    query: { project_id: projectId, include_completed: includeCompleted },
  })
}

export function create(
  projectId: string,
  name: string,
  estimatedSeconds: number | null,
): Promise<Task> {
  return request<Task>(inWorkspace('/tasks'), {
    method: 'POST',
    body: { project_id: projectId, name, estimated_seconds: estimatedSeconds },
  })
}

export interface TaskPatch {
  name?: string
  /** `null` clears the estimate. */
  estimated_seconds?: number | null
}

/** The completion state goes through `setCompleted`: the API keeps it apart. */
export function update(id: string, patch: TaskPatch): Promise<Task> {
  return request<Task>(inWorkspace(`/tasks/${id}`), { method: 'PATCH', body: patch })
}

export function setCompleted(id: string, completed: boolean): Promise<Task> {
  return request<Task>(inWorkspace(`/tasks/${id}`), {
    method: 'PATCH',
    body: { completed },
  })
}

/** Entries that had the task keep their time and lose the task. */
export function remove(id: string): Promise<void> {
  return request<void>(inWorkspace(`/tasks/${id}`), { method: 'DELETE' })
}
