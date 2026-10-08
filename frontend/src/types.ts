/** Shapes returned by the Hourtime API. */

/** `classic` - 1:05, `decimal` - 1.08, `improved` - 1:05:00. */
export type DurationFormat = 'classic' | 'decimal' | 'improved'

export interface User {
  id: string
  email: string
  display_name: string | null
  /** IANA name; null until a client reports its zone. */
  timezone: string | null
  /** 0 = Sunday ... 6 = Saturday, as `Date.getDay()`. */
  week_start: number
  duration_format: DurationFormat
  hour_cycle: 12 | 24
  created_at: string
}

export type ProfilePatch = Partial<
  Pick<User, 'display_name' | 'timezone' | 'week_start' | 'duration_format' | 'hour_cycle'>
>

export interface Tokens {
  access_token: string
  refresh_token: string
  token_type: string
  access_expires_at: string
  refresh_expires_at: string
}

export interface LoginResponse {
  user: User
  tokens: Tokens
}

export interface Client {
  id: string
  name: string
  archived: boolean
  created_at: string
  updated_at: string
}

export interface Tag {
  id: string
  name: string
  created_at: string
  updated_at: string
}

export interface Project {
  id: string
  name: string
  color: string
  client_id: string | null
  archived: boolean
  created_at: string
  updated_at: string
}

export interface TimeEntry {
  id: string
  project_id: string | null
  tag_ids: string[]
  description: string
  started_at: string
  /** Null while the timer is still running. */
  stopped_at: string | null
  /** Null for a running entry — the client ticks that number itself. */
  duration_seconds: number | null
  created_at: string
  updated_at: string
}

/** A description tracked before, with the project it was tracked under. */
export interface TimeEntrySuggestion {
  description: string
  project_id: string | null
  last_used_at: string
}

export interface TimeEntryPage {
  items: TimeEntry[]
  /** Whether another page exists. The API reports no total on purpose. */
  has_more: boolean
  limit: number
  offset: number
}

export interface ApiErrorBody {
  error: {
    code: string
    message: string
  }
}
