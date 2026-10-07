import { createToastManager } from 'reka-ui'

/** Rendered by UiToastHost; usable from stores and plain modules too. */
export const toastManager = createToastManager()

export const toast = {
  info(title: string, description?: string) {
    return toastManager.add({ title, description, status: 'info', type: 'background' })
  },
  success(title: string, description?: string) {
    return toastManager.add({ title, description, status: 'success', type: 'background' })
  },
  /** Errors stay longer: they usually ask the user to do something. */
  error(title: string, description?: string) {
    return toastManager.add({
      title,
      description,
      status: 'error',
      type: 'foreground',
      duration: 8000,
    })
  },
}
