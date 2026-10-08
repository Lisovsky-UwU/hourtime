/** Shapes returned by the Hourtime API. */

export interface User {
  id: string
  email: string
  created_at: string
}

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

export interface Project {
  id: string
  name: string
  color: string
  archived: boolean
  created_at: string
  updated_at: string
}

export interface TimeEntry {
  id: string
  project_id: string | null
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
