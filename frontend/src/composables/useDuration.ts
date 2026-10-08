import { useI18n } from 'vue-i18n'

import { usePreferencesStore } from '@/stores/preferences'
import { formatDuration } from '@/utils/duration'

/**
 * `duration(seconds)` in the profile's format. Read during render, so a new
 * format or language re-renders every caller.
 */
export function useDuration() {
  const preferences = usePreferencesStore()
  const { locale } = useI18n()
  return (seconds: number) => formatDuration(seconds, preferences.durationFormat, locale.value)
}
