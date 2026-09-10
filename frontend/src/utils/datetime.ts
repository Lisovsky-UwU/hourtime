/**
 * Bridges the API (ISO 8601 in UTC) and `<input type="datetime-local">`,
 * which only speaks wall-clock time in the viewer's own zone.
 */

function pad(value: number): string {
  return value.toString().padStart(2, '0')
}

/**
 * `step` for every datetime-local input in the app.
 *
 * Without it the control rounds to whole minutes, which silently rewrites the
 * times of every entry that gets edited — and makes an entry shorter than a
 * minute unsaveable, because its start and end collapse onto each other.
 */
export const DATETIME_STEP = '1'

/** ISO UTC -> `YYYY-MM-DDTHH:mm:ss` in local time. */
export function toLocalInput(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return ''
  return (
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}` +
    `T${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
  )
}

/** `YYYY-MM-DDTHH:mm[:ss]` in local time -> ISO UTC, or null if unparseable. */
export function fromLocalInput(value: string): string | null {
  if (!value) return null
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return null
  return date.toISOString()
}

/** Local `YYYY-MM-DD`, used to group and label entries by day. */
export function localDayKey(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return ''
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

export function startOfLocalDay(offsetDays = 0): Date {
  const date = new Date()
  date.setHours(0, 0, 0, 0)
  date.setDate(date.getDate() + offsetDays)
  return date
}
