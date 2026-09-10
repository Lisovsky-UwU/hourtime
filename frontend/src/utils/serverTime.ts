/**
 * Keeps the UI honest about elapsed time when the device clock is wrong.
 *
 * Every API response carries `X-Server-Time`; the difference from the local
 * clock is remembered so a running timer counts from the server's idea of now.
 */

let offsetMs = 0

export function syncFromHeader(header: string | null): void {
  if (!header) return
  const serverMs = Date.parse(header)
  if (Number.isNaN(serverMs)) return
  offsetMs = serverMs - Date.now()
}

export function serverNow(): number {
  return Date.now() + offsetMs
}

export function serverNowIso(): string {
  return new Date(serverNow()).toISOString()
}

/** Seconds between `startedAt` and the server's now, never negative. */
export function elapsedSeconds(startedAt: string): number {
  const started = Date.parse(startedAt)
  if (Number.isNaN(started)) return 0
  return Math.max(0, Math.floor((serverNow() - started) / 1000))
}
