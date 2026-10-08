import { request } from '@/api/client'
import type { LoginResponse, ProfilePatch, User } from '@/types'

export function register(email: string, password: string): Promise<User> {
  return request<User>('/auth/register', {
    method: 'POST',
    body: { email, password },
    auth: false,
  })
}

export function login(email: string, password: string): Promise<LoginResponse> {
  return request<LoginResponse>('/auth/login', {
    method: 'POST',
    body: { email, password },
    auth: false,
  })
}

export function me(): Promise<User> {
  return request<User>('/auth/me')
}

export function updateMe(patch: ProfilePatch): Promise<User> {
  return request<User>('/auth/me', { method: 'PATCH', body: patch })
}

/** Signs out every other device; this session stays. */
export function changePassword(currentPassword: string, newPassword: string): Promise<void> {
  return request<void>('/auth/me/password', {
    method: 'POST',
    body: { current_password: currentPassword, new_password: newPassword },
  })
}

export function logout(): Promise<void> {
  return request<void>('/auth/logout', { method: 'POST' })
}

export function logoutEverywhere(): Promise<void> {
  return request<void>('/auth/logout-all', { method: 'POST' })
}
