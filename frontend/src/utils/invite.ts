/**
 * An invite link is `/invite#<token>`: a fragment never reaches the server, so
 * the token stays out of access logs. While the visitor signs in or registers,
 * the token waits in session storage.
 */

const KEY = 'hourtime.invite'

export function inviteLink(token: string): string {
  return `${window.location.origin}/invite#${token}`
}

/** Moves a token from the address bar into storage and returns the pending one. */
export function pendingInvite(): string | null {
  const fromHash = window.location.hash.slice(1)
  try {
    if (fromHash) {
      sessionStorage.setItem(KEY, fromHash)
      history.replaceState(history.state, '', window.location.pathname)
    }
    return sessionStorage.getItem(KEY)
  } catch {
    return fromHash || null
  }
}

export function clearPendingInvite(): void {
  try {
    sessionStorage.removeItem(KEY)
  } catch {
    // Storage is off; nothing was kept.
  }
}
