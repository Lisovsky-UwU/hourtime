import { request } from '@/api/client'
import type { Project } from '@/types'

export interface ProjectPatch {
  name?: string
  color?: string
  /** `null` detaches the client. */
  client_id?: string | null
  archived?: boolean
  billable?: boolean
  /** Decimal string; `null` falls back to the workspace rate. */
  hourly_rate?: string | null
}

/** Everything a new project may start with besides its name and color. */
export type ProjectExtras = Pick<ProjectPatch, 'client_id' | 'billable' | 'hourly_rate'>

export function list(includeArchived = false): Promise<Project[]> {
  return request<Project[]>('/projects', { query: { include_archived: includeArchived } })
}

export function create(name: string, color: string, extras: ProjectExtras = {}): Promise<Project> {
  return request<Project>('/projects', { method: 'POST', body: { name, color, ...extras } })
}

/** Only the keys present in `patch` are changed. */
export function update(id: string, patch: ProjectPatch): Promise<Project> {
  return request<Project>(`/projects/${id}`, { method: 'PATCH', body: patch })
}

export function remove(id: string): Promise<void> {
  return request<void>(`/projects/${id}`, { method: 'DELETE' })
}
