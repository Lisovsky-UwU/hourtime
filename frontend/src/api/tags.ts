import { request } from '@/api/client'
import type { Tag } from '@/types'

export function list(): Promise<Tag[]> {
  return request<Tag[]>('/tags')
}

export function create(name: string): Promise<Tag> {
  return request<Tag>('/tags', { method: 'POST', body: { name } })
}

export function rename(id: string, name: string): Promise<Tag> {
  return request<Tag>(`/tags/${id}`, { method: 'PATCH', body: { name } })
}

/** The tag also comes off every entry that had it. */
export function remove(id: string): Promise<void> {
  return request<void>(`/tags/${id}`, { method: 'DELETE' })
}
