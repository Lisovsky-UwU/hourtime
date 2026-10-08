import { onMounted, onUnmounted } from 'vue'

/**
 * Single-key shortcuts, the way Toggl has them.
 *
 * Letters are matched by `event.code`, the physical key, so `n` still works
 * with a Russian layout where that key types "т". A key pressed while typing,
 * inside an open dialog, menu or list, or with a modifier is left alone.
 */
export type Hotkey = 'n' | 's' | '?'

function matches(event: KeyboardEvent): Hotkey | null {
  if (event.code === 'KeyN' && !event.shiftKey) return 'n'
  if (event.code === 'KeyS' && !event.shiftKey) return 's'
  // `?` lives on different keys in different layouts; Shift+/ is the US spot.
  if (event.key === '?' || (event.code === 'Slash' && event.shiftKey)) return '?'
  return null
}

function isTyping(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false
  if (target.isContentEditable) return true
  return ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName)
}

function isInsideOverlay(target: EventTarget | null): boolean {
  if (!(target instanceof Element)) return false
  // Focus sits in the overlay; also covers a press while it still animates out.
  return target.closest('[role="dialog"], [role="alertdialog"], [role="menu"], [role="listbox"]') !== null
}

export function useHotkeys(handlers: Partial<Record<Hotkey, () => void>>): void {
  function onKeydown(event: KeyboardEvent) {
    if (event.defaultPrevented || event.repeat || event.isComposing) return
    if (event.ctrlKey || event.metaKey || event.altKey) return
    if (isTyping(event.target) || isInsideOverlay(event.target)) return

    const key = matches(event)
    const handler = key ? handlers[key] : undefined
    if (!handler) return
    event.preventDefault()
    handler()
  }

  onMounted(() => window.addEventListener('keydown', onKeydown))
  onUnmounted(() => window.removeEventListener('keydown', onKeydown))
}
