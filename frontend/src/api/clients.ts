import { inWorkspace, request } from '@/api/client'
import type { Client } from '@/types'

export interface ClientPatch {
  name?: string
  archived?: boolean
}

export function list(includeArchived = false): Promise<Client[]> {
  return request<Client[]>(inWorkspace('/clients'), {
    query: { include_archived: includeArchived },
  })
}

export function create(name: string): Promise<Client> {
  return request<Client>(inWorkspace('/clients'), { method: 'POST', body: { name } })
}

/** Only the keys present in `patch` are changed. */
export function update(id: string, patch: ClientPatch): Promise<Client> {
  return request<Client>(inWorkspace(`/clients/${id}`), { method: 'PATCH', body: patch })
}

/** Its projects stay, without a client. */
export function remove(id: string): Promise<void> {
  return request<void>(inWorkspace(`/clients/${id}`), { method: 'DELETE' })
}
