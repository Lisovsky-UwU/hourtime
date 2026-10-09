/**
 * Report periods: inclusive ranges of calendar days written as `YYYY-MM-DD`.
 *
 * Days are wall-calendar dates, not instants: the server places entries into
 * them in the profile time zone. Here they are built from the browser's
 * calendar, which only matters around midnight when the two zones differ.
 */

export interface Period {
  from: string
  to: string
}

export type PresetKey =
  | 'this-week'
  | 'last-week'
  | 'this-month'
  | 'last-month'
  | 'this-year'
  | 'last-year'

export const PRESETS: PresetKey[] = [
  'this-week',
  'last-week',
  'this-month',
  'last-month',
  'this-year',
  'last-year',
]

function pad(value: number): string {
  return value.toString().padStart(2, '0')
}

export function toDateKey(date: Date): string {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

/** Local midnight of the day; `Date` only so that `Intl` can format it. */
export function parseDateKey(key: string): Date {
  const [year = 0, month = 1, day = 1] = key.split('-').map(Number)
  return new Date(year, month - 1, day)
}

export function isDateKey(value: unknown): value is string {
  return (
    typeof value === 'string' &&
    /^\d{4}-\d{2}-\d{2}$/.test(value) &&
    !Number.isNaN(parseDateKey(value).getTime())
  )
}

export function addDays(key: string, days: number): string {
  const date = parseDateKey(key)
  date.setDate(date.getDate() + days)
  return toDateKey(date)
}

/** Number of days in the range, both ends included. */
export function lengthInDays(period: Period): number {
  // Rounded: a day across a DST change is 23 or 25 hours long.
  return (
    Math.round(
      (parseDateKey(period.to).getTime() - parseDateKey(period.from).getTime()) / 86_400_000,
    ) + 1
  )
}

/** First day of the week that contains `key`; `weekStart` numbered as `getDay()`. */
export function weekStartOf(key: string, weekStart: number): string {
  const sinceStart = (parseDateKey(key).getDay() - weekStart + 7) % 7
  return addDays(key, -sinceStart)
}

export function weekOf(key: string, weekStart: number): Period {
  const from = weekStartOf(key, weekStart)
  return { from, to: addDays(from, 6) }
}

function monthOf(year: number, month: number): Period {
  return {
    from: toDateKey(new Date(year, month, 1)),
    to: toDateKey(new Date(year, month + 1, 0)),
  }
}

export function presetPeriod(preset: PresetKey, weekStart: number, today = new Date()): Period {
  const key = toDateKey(today)
  const year = today.getFullYear()
  const month = today.getMonth()
  switch (preset) {
    case 'this-week':
      return weekOf(key, weekStart)
    case 'last-week':
      return weekOf(addDays(key, -7), weekStart)
    case 'this-month':
      return monthOf(year, month)
    case 'last-month':
      return monthOf(year, month - 1)
    case 'this-year':
      return { from: `${year}-01-01`, to: `${year}-12-31` }
    case 'last-year':
      return { from: `${year - 1}-01-01`, to: `${year - 1}-12-31` }
  }
}

export function matchPreset(
  period: Period,
  weekStart: number,
  today = new Date(),
): PresetKey | null {
  return (
    PRESETS.find((preset) => {
      const candidate = presetPeriod(preset, weekStart, today)
      return candidate.from === period.from && candidate.to === period.to
    }) ?? null
  )
}

/**
 * The previous or next period of the same kind: a whole month stays a whole
 * month (October to September, not 31 days back), a whole year a year, and
 * anything else moves by its own length.
 */
export function shiftPeriod(period: Period, direction: -1 | 1): Period {
  const from = parseDateKey(period.from)
  const to = parseDateKey(period.to)
  const startsMonth = from.getDate() === 1
  const endsMonth = addDays(period.to, 1).endsWith('-01')

  if (startsMonth && endsMonth && from.getMonth() === 0 && to.getMonth() === 11) {
    const months = (to.getFullYear() - from.getFullYear() + 1) * 12
    return shiftMonths(from, to, months * direction)
  }
  if (startsMonth && endsMonth) {
    const months =
      (to.getFullYear() - from.getFullYear()) * 12 + to.getMonth() - from.getMonth() + 1
    return shiftMonths(from, to, months * direction)
  }
  const days = lengthInDays(period) * direction
  return { from: addDays(period.from, days), to: addDays(period.to, days) }
}

function shiftMonths(from: Date, to: Date, months: number): Period {
  return {
    from: toDateKey(new Date(from.getFullYear(), from.getMonth() + months, 1)),
    to: toDateKey(new Date(to.getFullYear(), to.getMonth() + months + 1, 0)),
  }
}

/** `6 - 12 Oct 2026` in the language's own range notation. */
export function formatPeriod(period: Period, locale: string): string {
  const format = new Intl.DateTimeFormat(locale, {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
  return format.formatRange(parseDateKey(period.from), parseDateKey(period.to))
}
