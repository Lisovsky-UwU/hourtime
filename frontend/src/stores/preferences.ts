import { ref, watch } from 'vue'
import { defineStore } from 'pinia'

import type { HourCycle } from '@/utils/timeOfDay'
import { detectHourCycle } from '@/utils/timeOfDay'

export type Theme = 'auto' | 'light' | 'dark'

const HOUR_CYCLE_KEY = 'hourtime.hourCycle'
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

function storedHourCycle(): HourCycle | null {
  const raw = read(HOUR_CYCLE_KEY)
  return raw === '12' || raw === '24' ? raw : null
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

/** Display preferences for this browser. Never leaves the device. */
export const usePreferencesStore = defineStore('preferences', () => {
  // Defaults to whatever this browser's locale would do, so most people never
  // have to touch the setting.
  const hourCycle = ref<HourCycle>(storedHourCycle() ?? detectHourCycle())
  const theme = ref<Theme>(storedTheme())
  const sidebarCollapsed = ref(read(SIDEBAR_KEY) === '1')

  watch(hourCycle, (value) => write(HOUR_CYCLE_KEY, value))
  watch(sidebarCollapsed, (value) => write(SIDEBAR_KEY, value ? '1' : '0'))

  watch(
    theme,
    (value) => {
      applyTheme(value)
      write(THEME_KEY, value)
    },
    { immediate: true },
  )

  return { hourCycle, theme, sidebarCollapsed }
})
