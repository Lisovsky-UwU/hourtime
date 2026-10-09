import { ref, watch } from 'vue'
import type { WatchSource } from 'vue'

import { messageFor } from '@/composables/useApiError'

/**
 * Loads a report whenever what it depends on changes.
 *
 * The previous report stays on screen while the next one loads (the page
 * dims it), so changing a filter does not flash a skeleton. Only the latest
 * request may write: quick filter clicks can finish out of order.
 */
export function useReportData<T>(source: WatchSource, fetch: () => Promise<T>) {
  const data = ref<T | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  let latest = 0

  async function load() {
    const id = ++latest
    loading.value = true
    error.value = null
    try {
      const result = await fetch()
      if (id === latest) data.value = result
    } catch (cause) {
      if (id === latest) error.value = messageFor(cause)
    } finally {
      if (id === latest) loading.value = false
    }
  }

  watch(source, load, { immediate: true, deep: true })

  return { data, loading, error, load }
}
