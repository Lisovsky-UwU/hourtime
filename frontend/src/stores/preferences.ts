import { ref, watch } from 'vue'
import { defineStore } from 'pinia'

import type { HourCycle } from '@/utils/timeOfDay'
import { detectHourCycle } from '@/utils/timeOfDay'

const STORAGE_KEY = 'hourtime.hourCycle'

function stored(): HourCycle | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw === '12' || raw === '24' ? raw : null
  } catch {
    return null
  }
}

/** Display preferences for this browser. Never leaves the device. */
export const usePreferencesStore = defineStore('preferences', () => {
  // Defaults to whatever this browser's locale would do, so most people never
  // have to touch the setting.
  const hourCycle = ref<HourCycle>(stored() ?? detectHourCycle())

  watch(hourCycle, (value) => {
    try {
      localStorage.setItem(STORAGE_KEY, value)
    } catch {
      // The choice just will not survive a reload.
    }
  })

  return { hourCycle }
})
