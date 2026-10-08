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

export function secondsBetween(from: string, to: string): number {
  return Math.max(0, Math.floor((Date.parse(to) - Date.parse(from)) / 1000))
}
