/** Duration formatting. Digits only — no words, so nothing here needs translating. */

function pad(value: number): string {
  return value.toString().padStart(2, '0')
}

/** `H:MM:SS`, the running-timer format. */
export function formatClock(totalSeconds: number): string {
  const seconds = Math.max(0, Math.floor(totalSeconds))
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  return `${hours}:${pad(minutes)}:${pad(seconds % 60)}`
}

export function secondsBetween(from: string, to: string): number {
  return Math.max(0, Math.floor((Date.parse(to) - Date.parse(from)) / 1000))
}
