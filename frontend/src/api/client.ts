/**
 * The single place that talks HTTP.
 *
 * Two things here are load-bearing:
 *  - refreshes are single-flight. The API rotates both tokens and treats a
 *    replayed refresh token as a leak, revoking every session — so two parallel
 *    refreshes would log the user out for real.
 *  - every response updates the server-clock offset used to tick timers.
 */

import type { ApiErrorBody, LoginResponse, Tokens } from '@/types'
import { syncFromHeader } from '@/utils/serverTime'

const BASE_URL = '/api/v1'
const STORAGE_KEY = 'hourtime.tokens'

export class ApiError extends Error {
  readonly status: number
  readonly code: string

  constructor(status: number, code: string, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }

  get isUnauthorized(): boolean {
    return this.status === 401
  }
}

/** An array is sent as a repeated key: `?tag_ids=a&tag_ids=b`. */
type QueryValue = string | number | boolean | string[] | null | undefined

export interface RequestOptions {
  method?: string
  body?: unknown
  query?: Record<string, QueryValue>
  /** Set false for endpoints that must not carry a bearer token. */
  auth?: boolean
}

function readStored(): Tokens | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as Tokens) : null
  } catch {
    // Private mode, disabled storage, or a corrupted value.
    return null
  }
}

let tokens: Tokens | null = readStored()
let refreshInFlight: Promise<Tokens> | null = null
const listeners = new Set<(next: Tokens | null) => void>()

export function getTokens(): Tokens | null {
  return tokens
}

export function setTokens(next: Tokens | null): void {
  tokens = next
  try {
    if (next) localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
    else localStorage.removeItem(STORAGE_KEY)
  } catch {
    // Session simply will not survive a reload; nothing else breaks.
  }
  listeners.forEach((listener) => listener(next))
}

/** Notifies when the session appears or disappears, including on a failed refresh. */
export function onTokensChanged(listener: (next: Tokens | null) => void): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

function buildUrl(path: string, query?: Record<string, QueryValue>): string {
  const url = new URL(`${BASE_URL}${path}`, window.location.origin)
  for (const [key, value] of Object.entries(query ?? {})) {
    if (Array.isArray(value)) {
      for (const item of value) url.searchParams.append(key, item)
    } else if (value !== null && value !== undefined && value !== '') {
      url.searchParams.set(key, String(value))
    }
  }
  return url.pathname + url.search
}

async function toApiError(response: Response): Promise<ApiError> {
  let code = 'http_error'
  let message = response.statusText || `Request failed with status ${response.status}`
  try {
    const body = (await response.json()) as ApiErrorBody
    if (body?.error?.code) {
      code = body.error.code
      message = body.error.message
    }
  } catch {
    // Not a JSON error envelope — keep the status-based message.
  }
  return new ApiError(response.status, code, message)
}

async function send(
  path: string,
  options: RequestOptions,
  accessToken: string | null,
): Promise<Response> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (options.body !== undefined) headers['Content-Type'] = 'application/json'
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`

  let response: Response
  try {
    response = await fetch(buildUrl(path, options.query), {
      method: options.method ?? 'GET',
      headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
    })
  } catch (cause) {
    throw new ApiError(0, 'network_error', (cause as Error).message)
  }

  syncFromHeader(response.headers.get('X-Server-Time'))
  return response
}

function refreshTokens(): Promise<Tokens> {
  if (!refreshInFlight) {
    const current = tokens
    refreshInFlight = (async () => {
      try {
        if (!current) throw new ApiError(401, 'invalid_token', 'Not signed in')
        const response = await send(
          '/auth/refresh',
          { method: 'POST', body: { refresh_token: current.refresh_token }, auth: false },
          null,
        )
        if (!response.ok) {
          // The refresh token is gone for good; drop the session.
          setTokens(null)
          throw await toApiError(response)
        }
        const data = (await response.json()) as LoginResponse
        setTokens(data.tokens)
        return data.tokens
      } finally {
        refreshInFlight = null
      }
    })()
  }
  return refreshInFlight
}

/** Sends with the access token, refreshing it once on a 401; throws on any error status. */
async function authorized(path: string, options: RequestOptions): Promise<Response> {
  const needsAuth = options.auth !== false
  if (needsAuth && !tokens) {
    throw new ApiError(401, 'invalid_token', 'Not signed in')
  }

  let response = await send(path, options, needsAuth ? (tokens?.access_token ?? null) : null)

  if (response.status === 401 && needsAuth) {
    const refreshed = await refreshTokens()
    response = await send(path, options, refreshed.access_token)
  }

  if (!response.ok) throw await toApiError(response)
  return response
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const response = await authorized(path, options)
  if (response.status === 204) return undefined as T

  const text = await response.text()
  return (text ? JSON.parse(text) : null) as T
}

/**
 * Saves a file the API sends as an attachment. A plain link cannot carry the
 * bearer token, so the file is fetched here and handed to the browser.
 */
export async function download(path: string, options: RequestOptions = {}): Promise<void> {
  const response = await authorized(path, options)
  const disposition = response.headers.get('Content-Disposition') ?? ''
  const name = /filename="([^"]+)"/.exec(disposition)?.[1] ?? 'download'

  const url = URL.createObjectURL(await response.blob())
  const link = document.createElement('a')
  link.href = url
  link.download = name
  link.click()
  // Revoked on the next tick: the click only starts the download.
  window.setTimeout(() => URL.revokeObjectURL(url))
}
