import { request } from '@/api/client'
import type { Project } from '@/types'

export interface ProjectPatch {
  name?: string
  color?: string
  /** `null` detaches the client. */
  client_id?: string | null
  archived?: boolean
}

export function list(includeArchived = false): Promise<Project[]> {
  return request<Project[]>('/projects', { query: { include_archived: includeArchived } })
}

export function create(
  name: string,
  color: string,
  clientId: string | null = null,
): Promise<Project> {
  return request<Project>('/projects', {
    method: 'POST',
    body: { name, color, client_id: clientId },
  })
}

/** Only the keys present in `patch` are changed. */
export function update(id: string, patch: ProjectPatch): Promise<Project> {
  return request<Project>(`/projects/${id}`, { method: 'PATCH', body: patch })
}

export function remove(id: string): Promise<void> {
  return request<void>(`/projects/${id}`, { method: 'DELETE' })
}
