import { computed, ref, watch } from 'vue'
import { defineStore } from 'pinia'

import { useAuthStore } from '@/stores/auth'
import type { DurationFormat } from '@/types'
import type { HourCycle } from '@/utils/timeOfDay'
import { detectHourCycle } from '@/utils/timeOfDay'

export type Theme = 'auto' | 'light' | 'dark'

// The inline script in index.html reads the same key before the app loads.
const THEME_KEY = 'hourtime.theme'
const SIDEBAR_KEY = 'hourtime.sidebarCollapsed'

function read(key: string): string | null {
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

function write(key: string, value: string) {
  try {
    localStorage.setItem(key, value)
  } catch {
    // The choice just will not survive a reload.
  }
}

function storedTheme(): Theme {
  const raw = read(THEME_KEY)
  return raw === 'light' || raw === 'dark' ? raw : 'auto'
}

/** "auto" leaves the attribute off, so `color-scheme` follows the system. */
function applyTheme(theme: Theme) {
  const root = document.documentElement
  if (theme === 'auto') delete root.dataset.theme
  else root.dataset.theme = theme
}

/**
 * Display preferences. Theme and sidebar belong to this browser. Hour cycle,
 * week start and duration format come from the profile, so every device shows
 * the same numbers; they are read-only here - change them with
 * `auth.updateProfile`.
 */
export const usePreferencesStore = defineStore('preferences', () => {
  const auth = useAuthStore()

  const theme = ref<Theme>(storedTheme())
  const sidebarCollapsed = ref(read(SIDEBAR_KEY) === '1')

  const hourCycle = computed<HourCycle>(() =>
    auth.user ? (String(auth.user.hour_cycle) as HourCycle) : detectHourCycle(),
  )
  const weekStart = computed(() => auth.user?.week_start ?? 1)
  const durationFormat = computed<DurationFormat>(() => auth.user?.duration_format ?? 'classic')

  watch(sidebarCollapsed, (value) => write(SIDEBAR_KEY, value ? '1' : '0'))

  watch(
    theme,
    (value) => {
      applyTheme(value)
      write(THEME_KEY, value)
    },
    { immediate: true },
  )

  return { theme, sidebarCollapsed, hourCycle, weekStart, durationFormat }
})
