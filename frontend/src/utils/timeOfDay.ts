/**
 * Times are typed, not picked.
 *
 * The row editor accepts whatever shape a person naturally types — `9`, `930`,
 * `9:30`, `21.26.55`, `2:05 pm` — and renders it back in the hour cycle the
 * user chose. Seconds survive a round trip: they are shown only when they are
 * not zero, so a three-second entry stays three seconds instead of collapsing
 * onto its own start.
 */

export type HourCycle = '12' | '24'

export interface TimeOfDay {
  hours: number
  minutes: number
  seconds: number
  /** Days past the entry's start date. Non-zero only for entries spanning midnight. */
  dayOffset: number
}

const PATTERN =
  /^\s*(\d{1,2})(?:[:.\s]?(\d{2}))?(?:[:.\s]?(\d{2}))?\s*(am|pm|a|p)?\s*(?:\+\s*(\d+)\s*d?)?\s*$/i

function pad(value: number): string {
  return value.toString().padStart(2, '0')
}

export function parseTimeOfDay(input: string): TimeOfDay | null {
  const match = PATTERN.exec(input)
  if (!match) return null

  let hours = Number(match[1])
  const minutes = Number(match[2] ?? 0)
  const seconds = Number(match[3] ?? 0)
  const meridiem = match[4]?.[0]?.toLowerCase()
  const dayOffset = Number(match[5] ?? 0)

  if (meridiem) {
    if (hours < 1 || hours > 12) return null
    if (meridiem === 'p' && hours !== 12) hours += 12
    if (meridiem === 'a' && hours === 12) hours = 0
  }

  if (hours > 23 || minutes > 59 || seconds > 59) return null
  return { hours, minutes, seconds, dayOffset }
}

/**
 * Hours and minutes only: seconds are noise in a list of entries. They are
 * still stored and kept unless the user types a different time.
 */
export function formatTimeOfDay(time: TimeOfDay, cycle: HourCycle): string {
  let text: string

  if (cycle === '12') {
    const meridiem = time.hours < 12 ? 'AM' : 'PM'
    const hour = time.hours % 12 === 0 ? 12 : time.hours % 12
    text = `${hour}:${pad(time.minutes)} ${meridiem}`
  } else {
    text = `${pad(time.hours)}:${pad(time.minutes)}`
  }

  return time.dayOffset > 0 ? `${text} +${time.dayOffset}d` : text
}

export function sameTimeOfDay(a: TimeOfDay, b: TimeOfDay): boolean {
  return (
    a.hours === b.hours &&
    a.minutes === b.minutes &&
    a.seconds === b.seconds &&
    a.dayOffset === b.dayOffset
  )
}

/** `YYYY-MM-DD` in local time, the value an `<input type="date">` expects. */
export function toDateInput(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return ''
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

/** Wall-clock time of `iso`, counted in days from `baseIso`'s local date. */
export function toTimeOfDay(iso: string, baseIso = iso): TimeOfDay {
  const date = new Date(iso)
  const base = new Date(baseIso)
  const startOfBase = new Date(base.getFullYear(), base.getMonth(), base.getDate())
  const startOfDate = new Date(date.getFullYear(), date.getMonth(), date.getDate())
  const dayOffset = Math.round(
    (startOfDate.getTime() - startOfBase.getTime()) / (24 * 60 * 60 * 1000),
  )
  return {
    hours: date.getHours(),
    minutes: date.getMinutes(),
    seconds: date.getSeconds(),
    dayOffset: Math.max(0, dayOffset),
  }
}

/** `YYYY-MM-DD` plus a wall-clock time -> ISO UTC, or null if the date is unusable. */
export function combine(dateInput: string, time: TimeOfDay): string | null {
  const parts = dateInput.split('-').map(Number)
  const [year, month, day] = parts
  if (parts.length !== 3 || year === undefined || month === undefined || day === undefined) {
    return null
  }
  if ([year, month, day].some(Number.isNaN)) return null

  const result = new Date(
    year,
    month - 1,
    day + time.dayOffset,
    time.hours,
    time.minutes,
    time.seconds,
    0,
  )
  return Number.isNaN(result.getTime()) ? null : result.toISOString()
}

/**
 * The end of an entry that carries only a start date.
 *
 * An end earlier than the start means the entry ran past midnight, so it lands
 * on the following day — unless the typed value already said how many days.
 */
export function combineEnd(
  dateInput: string,
  start: TimeOfDay,
  end: TimeOfDay,
): string | null {
  const startedAt = combine(dateInput, start)
  const candidate = combine(dateInput, end)
  if (!startedAt || !candidate) return null

  if (end.dayOffset === 0 && Date.parse(candidate) <= Date.parse(startedAt)) {
    return combine(dateInput, { ...end, dayOffset: 1 })
  }
  return candidate
}

/** The cycle this browser would use, so the default matches the user's habits. */
export function detectHourCycle(): HourCycle {
  const resolved = new Intl.DateTimeFormat(undefined, { hour: 'numeric' }).resolvedOptions()
  if (resolved.hourCycle) return resolved.hourCycle.startsWith('h1') ? '12' : '24'
  return resolved.hour12 ? '12' : '24'
}
