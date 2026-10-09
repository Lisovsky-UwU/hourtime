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

export interface Workspace {
  id: string
  name: string
  /** Decimal string such as "150.00", for billable entries of projects without a rate. */
  default_hourly_rate: string | null
  /** ISO 4217 code: one currency for every rate and amount. */
  currency: string
}

export type WorkspacePatch = Partial<Pick<Workspace, 'default_hourly_rate' | 'currency'>>

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
  /** What new entries on this project start as. */
  billable: boolean
  /** Decimal string such as "150.00"; null - the workspace rate applies. */
  hourly_rate: string | null
  archived: boolean
  created_at: string
  updated_at: string
}

export interface TimeEntry {
  id: string
  project_id: string | null
  tag_ids: string[]
  description: string
  billable: boolean
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

/** Durations in whole seconds, amounts as decimal strings (`"1503.33"`) in the workspace currency. */
export interface ReportTotals {
  duration: number
  billable_duration: number
  amount: string
  entries: number
}

export interface ReportDay {
  /** `YYYY-MM-DD` in the profile time zone. */
  date: string
  duration: number
  billable_duration: number
  amount: string
}

/** A project, client, tag or description; `id` and `name` are null for "without". */
export interface ReportGroup extends ReportTotals {
  id: string | null
  name: string | null
  color: string | null
  client_name: string | null
}

export interface SummaryReport {
  currency: string
  totals: ReportTotals
  /** Every day of the range in order, empty days as zeros; null without a range. */
  by_day: ReportDay[] | null
  groups: (ReportGroup & { subgroups: ReportGroup[] })[]
}

export interface DetailedReportItem {
  id: string
  description: string
  project: { id: string; name: string; color: string } | null
  client: { id: string; name: string } | null
  tags: { id: string; name: string }[]
  billable: boolean
  started_at: string
  stopped_at: string
  duration: number
  /** Null unless the entry is billable and has a rate. */
  amount: string | null
}

export interface DetailedReport {
  currency: string
  /** Over everything the filters match, not just this page. */
  totals: ReportTotals
  items: DetailedReportItem[]
  has_more: boolean
  limit: number
  offset: number
}

export interface WeeklyReport {
  currency: string
  days: string[]
  totals: ReportTotals & { days: number[] }
  rows: (ReportGroup & { days: number[] })[]
}

export interface ApiErrorBody {
  error: {
    code: string
    message: string
  }
}
