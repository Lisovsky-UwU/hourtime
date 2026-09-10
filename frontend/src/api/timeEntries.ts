import { request } from '@/api/client'
import type { TimeEntry, TimeEntryPage } from '@/types'

export interface ListQuery {
  started_from?: string
  started_to?: string
  project_id?: string
  limit?: number
  offset?: number
}

export interface StartPayload {
  project_id?: string | null
  description?: string
  /** Omit to start from the server's now. */
  started_at?: string
}

/**
 * Only the keys present are changed. `project_id: null` detaches the project,
 * which is why the type allows null explicitly.
 */
export interface EntryPatch {
  project_id?: string | null
  description?: string
  started_at?: string
  stopped_at?: string
}

export function list(query: ListQuery = {}): Promise<TimeEntryPage> {
  return request<TimeEntryPage>('/time-entries', { query: { ...query } })
}

export function current(): Promise<TimeEntry | null> {
  return request<TimeEntry | null>('/time-entries/current')
}

export function start(payload: StartPayload = {}): Promise<TimeEntry> {
  return request<TimeEntry>('/time-entries/start', { method: 'POST', body: payload })
}

export function stop(id: string, stoppedAt?: string): Promise<TimeEntry> {
  return request<TimeEntry>(`/time-entries/${id}/stop`, {
    method: 'POST',
    body: stoppedAt ? { stopped_at: stoppedAt } : {},
  })
}

export function create(payload: {
  started_at: string
  stopped_at: string
  project_id?: string | null
  description?: string
}): Promise<TimeEntry> {
  return request<TimeEntry>('/time-entries', { method: 'POST', body: payload })
}

export function update(id: string, patch: EntryPatch): Promise<TimeEntry> {
  return request<TimeEntry>(`/time-entries/${id}`, { method: 'PATCH', body: patch })
}

export function remove(id: string): Promise<void> {
  return request<void>(`/time-entries/${id}`, { method: 'DELETE' })
}
