import { request } from '@/api/client'
import type { Workspace, WorkspacePatch } from '@/types'

/** The workspace everything is tracked in, until workspaces can be picked. */
export function current(): Promise<Workspace> {
  return request<Workspace>('/workspaces/current')
}

/** Only the keys present are changed; `default_hourly_rate: null` removes the rate. */
export function updateCurrent(patch: WorkspacePatch): Promise<Workspace> {
  return request<Workspace>('/workspaces/current', { method: 'PATCH', body: patch })
}
