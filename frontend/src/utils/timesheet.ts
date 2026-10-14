/**
 * The timesheet's cell edit: a person types the day's new total for one row,
 * and this works out which entries to create, shorten or delete to get there.
 *
 * More time is always a new entry for the difference, so existing entries
 * keep their times. Less time comes off the latest entries first: the last one
 * is cut short, and one that is not long enough goes away whole.
 */

export interface CellEntry {
  id: string
  started_at: string
  stopped_at: string
}

export type CellChange =
  | { kind: 'create'; startedAt: number; stoppedAt: number }
  | { kind: 'shorten'; id: string; stoppedAt: number }
  | { kind: 'delete'; id: string }

const HOUR_MS = 3_600_000
const DAY_SECONDS = 24 * 3600
/** Where a new entry goes on a day that has none yet. */
const WORKDAY_START_HOUR = 9

/**
 * Seconds from what is typed into a cell: `1:30`, `1:30:15`, `1.5` or `1,5`
 * (hours), `2` (hours). Empty is zero, which clears the cell. Null when the
 * text is not a duration or is longer than a day.
 */
export function parseDuration(input: string): number | null {
  const text = input.trim()
  if (!text) return 0

  let seconds: number
  const clock = /^(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?$/.exec(text)
  if (clock) {
    const [, hours = '0', minutes = '0', secs = '0'] = clock
    if (Number(minutes) > 59 || Number(secs) > 59) return null
    seconds = Number(hours) * 3600 + Number(minutes) * 60 + Number(secs)
  } else if (/^\d{1,2}(?:[.,]\d+)?$/.test(text)) {
    seconds = Math.round(Number(text.replace(',', '.')) * 3600)
  } else {
    return null
  }
  return seconds <= DAY_SECONDS ? seconds : null
}

/**
 * Changes that bring the cell's `entries` (stopped ones only) to `target`
 * seconds, in the order they should be sent. Null when the extra time does not
 * fit: on today it would have to end after `now` and start before midnight.
 *
 * `dayStart` and `dayEnd` are the local midnights around the cell's day,
 * `lastEnd` the latest end of any entry started that day (any row), so a new
 * entry follows the day's work. It must still start on that day, or it would
 * count on the next one: after a day that ran past midnight it ends at midnight.
 */
export function planCellChange(
  entries: CellEntry[],
  target: number,
  day: { dayStart: number; dayEnd: number; lastEnd: number | null; now: number },
): CellChange[] | null {
  const lengthOf = (entry: CellEntry) => Date.parse(entry.stopped_at) - Date.parse(entry.started_at)
  const current = entries.reduce((sum, entry) => sum + lengthOf(entry), 0)
  const delta = target * 1000 - current
  if (Math.abs(delta) < 1000) return []

  if (delta > 0) {
    let startedAt = day.lastEnd ?? day.dayStart + WORKDAY_START_HOUR * HOUR_MS
    if (startedAt >= day.dayEnd) startedAt = day.dayEnd - delta
    if (startedAt + delta > day.now) startedAt = day.now - delta
    if (startedAt < day.dayStart) return null
    return [{ kind: 'create', startedAt, stoppedAt: startedAt + delta }]
  }

  const changes: CellChange[] = []
  let remove = -delta
  const latestFirst = [...entries].sort(
    (a, b) => Date.parse(b.started_at) - Date.parse(a.started_at),
  )
  for (const entry of latestFirst) {
    const length = lengthOf(entry)
    if (length > remove) {
      changes.push({
        kind: 'shorten',
        id: entry.id,
        stoppedAt: Date.parse(entry.stopped_at) - remove,
      })
      break
    }
    changes.push({ kind: 'delete', id: entry.id })
    remove -= length
    if (remove <= 0) break
  }
  return changes
}
