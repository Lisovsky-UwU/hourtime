import { download, request } from '@/api/client'
import type { DetailedReport, SummaryReport, WeeklyReport } from '@/types'

export type SummaryGrouping = 'project' | 'client' | 'tag' | 'description'
export type DetailedSort = 'started_at' | 'duration' | 'description' | 'project'

/**
 * Filters shared by every report. A list and its "without" flag are joined by
 * OR: projects A and B plus "without project" keeps all three kinds of entry.
 */
export interface ReportFilters {
  /** `YYYY-MM-DD`, both or neither; dates are days in the profile time zone. */
  start_date?: string
  end_date?: string
  project_ids?: string[]
  without_project?: boolean
  client_ids?: string[]
  without_client?: boolean
  tag_ids?: string[]
  without_tags?: boolean
  billable?: boolean
  description?: string
}

export function summary(
  filters: ReportFilters,
  groupBy: SummaryGrouping,
  subgroupBy: SummaryGrouping | null,
): Promise<SummaryReport> {
  return request<SummaryReport>('/reports/summary', {
    query: { ...filters, group_by: groupBy, subgroup_by: subgroupBy },
  })
}

export function detailed(
  filters: ReportFilters,
  sort: DetailedSort,
  order: 'asc' | 'desc',
  limit: number,
  offset: number,
): Promise<DetailedReport> {
  return request<DetailedReport>('/reports/detailed', {
    query: { ...filters, sort, order, limit, offset },
  })
}

export function summaryCsv(
  filters: ReportFilters,
  groupBy: SummaryGrouping,
  subgroupBy: SummaryGrouping | null,
): Promise<void> {
  return download('/reports/summary.csv', {
    query: { ...filters, group_by: groupBy, subgroup_by: subgroupBy },
  })
}

/** Every entry the filters let through, not just the loaded pages. */
export function detailedCsv(
  filters: ReportFilters,
  sort: DetailedSort,
  order: 'asc' | 'desc',
): Promise<void> {
  return download('/reports/detailed.csv', { query: { ...filters, sort, order } })
}

/** At most 7 days; the caller aligns them to the profile's first day of the week. */
export function weekly(
  filters: ReportFilters,
  groupBy: 'project' | 'client',
): Promise<WeeklyReport> {
  return request<WeeklyReport>('/reports/weekly', { query: { ...filters, group_by: groupBy } })
}
