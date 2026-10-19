import { inWorkspace, request } from '@/api/client'
import type {
  Invite,
  InvitePreview,
  IssuedInvite,
  Member,
  MemberRole,
  Workspace,
  WorkspacePatch,
} from '@/types'

/** The workspace this tab works in. */
export function current(): Promise<Workspace> {
  return request<Workspace>(inWorkspace(''))
}

/** Only the keys present are changed; `default_hourly_rate: null` removes the rate. */
export function updateCurrent(patch: WorkspacePatch): Promise<Workspace> {
  return request<Workspace>(inWorkspace(''), { method: 'PATCH', body: patch })
}

export function members(): Promise<Member[]> {
  return request<Member[]>(inWorkspace('/members'))
}

export function setRole(userId: string, role: MemberRole): Promise<void> {
  return request<void>(inWorkspace(`/members/${userId}`), { method: 'PATCH', body: { role } })
}

/** Removes someone, or leaves the workspace when it is the caller's own id. */
export function removeMember(userId: string): Promise<void> {
  return request<void>(inWorkspace(`/members/${userId}`), { method: 'DELETE' })
}

export function invites(): Promise<Invite[]> {
  return request<Invite[]>(inWorkspace('/invites'))
}

export function createInvite(): Promise<IssuedInvite> {
  return request<IssuedInvite>(inWorkspace('/invites'), { method: 'POST', body: {} })
}

export function revokeInvite(id: string): Promise<void> {
  return request<void>(inWorkspace(`/invites/${id}`), { method: 'DELETE' })
}

/** The token goes in the body: URLs end up in access logs. */
export function previewInvite(token: string): Promise<InvitePreview> {
  return request<InvitePreview>('/invites/preview', {
    method: 'POST',
    body: { token },
    auth: false,
  })
}

export function acceptInvite(token: string): Promise<Workspace> {
  return request<Workspace>('/invites/accept', { method: 'POST', body: { token } })
}
