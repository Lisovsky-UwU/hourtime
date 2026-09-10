import { ref } from 'vue'

import { ApiError } from '@/api/client'
import { i18n } from '@/i18n'

/**
 * Turns a thrown error into something a person can read.
 *
 * The API's error codes are stable, so they get proper translations; anything
 * unrecognised falls back to the server's own message rather than a shrug.
 */
export function messageFor(error: unknown): string {
  const { t, te } = i18n.global
  if (error instanceof ApiError) {
    // A validation failure names the field that is wrong, and that detail is
    // the whole point — "check the values and try again" tells the user
    // nothing. The server text is English-only for now; that is a better
    // trade than hiding the reason.
    if (error.code === 'validation_error' && error.message) return error.message

    const key = `errors.${error.code}`
    return te(key) ? t(key) : error.message
  }
  return t('errors.unknown')
}

/** Shared "run this, show the error if it fails" state for forms and dialogs. */
export function useAsyncAction() {
  const busy = ref(false)
  const error = ref<string | null>(null)

  async function run<T>(action: () => Promise<T>): Promise<T | undefined> {
    busy.value = true
    error.value = null
    try {
      return await action()
    } catch (cause) {
      error.value = messageFor(cause)
      return undefined
    } finally {
      busy.value = false
    }
  }

  return { busy, error, run }
}
