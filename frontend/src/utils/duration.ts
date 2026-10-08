/** Duration formatting. Digits only — no words, so nothing here needs translating. */

function pad(value: number): string {
  return value.toString().padStart(2, '0')
}

/** `H:MM`, for every duration and total. Seconds are left out on purpose. */
export function formatClock(totalSeconds: number): string {
  const minutesTotal = Math.floor(Math.max(0, totalSeconds) / 60)
  const hours = Math.floor(minutesTotal / 60)
  return `${hours}:${pad(minutesTotal % 60)}`
}

export function secondsBetween(from: string, to: string): number {
  return Math.max(0, Math.floor((Date.parse(to) - Date.parse(from)) / 1000))
}
