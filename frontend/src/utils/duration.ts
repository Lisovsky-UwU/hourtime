/** Duration formatting. Digits only — no words, so nothing here needs translating. */

import type { DurationFormat } from '@/types'

function pad(value: number): string {
  return value.toString().padStart(2, '0')
}

/** `H:MM`, the classic format. Seconds are left out on purpose. */
export function formatClock(totalSeconds: number): string {
  const minutesTotal = Math.floor(Math.max(0, totalSeconds) / 60)
  const hours = Math.floor(minutesTotal / 60)
  return `${hours}:${pad(minutesTotal % 60)}`
}

/**
 * A duration in the profile's format: `classic` 1:05, `decimal` 1.08 (hours,
 * with the locale's decimal mark), `improved` 1:05:00.
 */
export function formatDuration(
  totalSeconds: number,
  format: DurationFormat,
  locale: string,
): string {
  const seconds = Math.floor(Math.max(0, totalSeconds))
  if (format === 'decimal') {
    return new Intl.NumberFormat(locale, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
      useGrouping: false,
    }).format(seconds / 3600)
  }
  if (format === 'improved') {
    const hours = Math.floor(seconds / 3600)
    return `${hours}:${pad(Math.floor(seconds / 60) % 60)}:${pad(seconds % 60)}`
  }
  return formatClock(seconds)
}

/**
 * Seconds from a typed duration: `1:30`, `1:30:15`, `1.5` or `1,5` (hours),
 * `2` (hours). Empty is zero. Null when the text is not a duration. No upper
 * bound: an estimate may be longer than a day, unlike a timesheet cell.
 */
export function parseDurationText(input: string): number | null {
  const text = input.trim()
  if (!text) return 0

  const clock = /^(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?$/.exec(text)
  if (clock) {
    const [, hours = '0', minutes = '0', secs = '0'] = clock
    if (Number(minutes) > 59 || Number(secs) > 59) return null
    return Number(hours) * 3600 + Number(minutes) * 60 + Number(secs)
  }
  if (/^\d{1,2}(?:[.,]\d+)?$/.test(text)) return Math.round(Number(text.replace(',', '.')) * 3600)
  return null
}

export function secondsBetween(from: string, to: string): number {
  return Math.max(0, Math.floor((Date.parse(to) - Date.parse(from)) / 1000))
}
