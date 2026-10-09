import { computed } from 'vue'
import type { LocationQueryRaw, LocationQueryValue } from 'vue-router'
import { useRoute, useRouter } from 'vue-router'

import type { DetailedSort, ReportFilters, SummaryGrouping } from '@/api/reports'
import { usePreferencesStore } from '@/stores/preferences'
import type { Period } from '@/utils/period'
import { isDateKey, presetPeriod, weekOf } from '@/utils/period'

export type ReportView = 'summary' | 'detailed' | 'weekly'

/** In a project, client or tag list it stands for "without one"; never a real id. */
export const NONE = 'none'

const GROUPINGS: SummaryGrouping[] = ['project', 'client', 'tag', 'description']
const SORTS: DetailedSort[] = ['started_at', 'duration', 'description', 'project']

export interface ReportState {
  /** Null means all time; the weekly report never gets null. */
  period: Period | null
  projects: string[]
  clients: string[]
  tags: string[]
  billable: 'yes' | 'no' | null
  description: string
  groupBy: SummaryGrouping
  subgroupBy: SummaryGrouping | null
  sort: DetailedSort
  order: 'asc' | 'desc'
}

type QueryParam = LocationQueryValue | LocationQueryValue[] | undefined

function list(value: QueryParam): string[] {
  const items = Array.isArray(value) ? value : value ? [value] : []
  return items.filter((item): item is string => typeof item === 'string' && item !== '')
}

function single(value: QueryParam): string | null {
  const item = Array.isArray(value) ? value[0] : value
  return typeof item === 'string' ? item : null
}

function oneOf<T extends string>(value: string | null, options: readonly T[]): T | null {
  return options.includes(value as T) ? (value as T) : null
}

/** A list with the NONE marker split into ids and the "without" flag the API wants. */
function split(items: string[]): [string[] | undefined, boolean | undefined] {
  const ids = items.filter((item) => item !== NONE)
  return [ids.length ? ids : undefined, items.includes(NONE) || undefined]
}

/**
 * The report the page shows, kept in the URL so that a report can be
 * bookmarked, shared between devices and survives a reload. Values the URL
 * does not carry fall back to defaults, and those defaults are left out of
 * the URL to keep it short.
 */
export function useReportQuery() {
  const route = useRoute()
  const router = useRouter()
  const preferences = usePreferencesStore()

  const view = computed<ReportView>(
    () =>
      oneOf(single(route.params.view as QueryParam), ['summary', 'detailed', 'weekly'] as const) ??
      'summary',
  )

  const state = computed<ReportState>(() => {
    const query = route.query
    const from = single(query.from)
    const to = single(query.to)
    let period: Period | null =
      isDateKey(from) && isDateKey(to) && from <= to
        ? { from, to }
        : single(query.all) === '1'
          ? null
          : presetPeriod('this-week', preferences.weekStart)
    // A week report of a month makes no sense: it shows the week the period starts in.
    if (view.value === 'weekly') {
      period = weekOf(
        period?.from ?? presetPeriod('this-week', preferences.weekStart).from,
        preferences.weekStart,
      )
    }

    const groupBy = oneOf(single(query.group), GROUPINGS) ?? 'project'
    const sub = single(query.sub)
    const subgroupBy = sub === NONE ? null : (oneOf(sub, GROUPINGS) ?? 'description')

    return {
      period,
      projects: list(query.project),
      clients: list(query.client),
      tags: list(query.tag),
      billable: oneOf(single(query.billable), ['yes', 'no'] as const),
      description: single(query.q) ?? '',
      groupBy,
      // The server refuses a subgroup equal to the group.
      subgroupBy: subgroupBy === groupBy ? null : subgroupBy,
      sort: oneOf(single(query.sort), SORTS) ?? 'started_at',
      order: single(query.order) === 'asc' ? 'asc' : 'desc',
    }
  })

  const filters = computed<ReportFilters>(() => {
    const current = state.value
    const [projectIds, withoutProject] = split(current.projects)
    const [clientIds, withoutClient] = split(current.clients)
    const [tagIds, withoutTags] = split(current.tags)
    return {
      start_date: current.period?.from,
      end_date: current.period?.to,
      project_ids: projectIds,
      without_project: withoutProject,
      client_ids: clientIds,
      without_client: withoutClient,
      tag_ids: tagIds,
      without_tags: withoutTags,
      billable: current.billable === null ? undefined : current.billable === 'yes',
      description: current.description.trim() || undefined,
    }
  })

  const filtered = computed(() => {
    const current = state.value
    return (
      current.projects.length + current.clients.length + current.tags.length > 0 ||
      current.billable !== null ||
      current.description.trim() !== ''
    )
  })

  function replace(query: LocationQueryRaw) {
    void router.replace({ query })
  }

  function setPeriod(period: Period | null) {
    const { from: _from, to: _to, all: _all, ...rest } = route.query
    replace(period ? { ...rest, from: period.from, to: period.to } : { ...rest, all: '1' })
  }

  /** `undefined`, empty strings and empty lists drop the key. */
  function patch(values: Record<string, string | string[] | null | undefined>) {
    const next: LocationQueryRaw = { ...route.query }
    for (const [key, value] of Object.entries(values)) {
      if (
        value === undefined ||
        value === null ||
        value === '' ||
        (Array.isArray(value) && !value.length)
      ) {
        delete next[key]
      } else {
        next[key] = value
      }
    }
    replace(next)
  }

  function clearFilters() {
    patch({ project: null, client: null, tag: null, billable: null, q: null })
  }

  /** Same report, other view; the filters travel along in the query. */
  function viewLink(target: ReportView) {
    return { name: 'reports', params: { view: target }, query: route.query }
  }

  return { view, state, filters, filtered, setPeriod, patch, clearFilters, viewLink }
}
