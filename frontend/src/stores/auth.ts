import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import * as authApi from '@/api/auth'
import { getTokens, onTokensChanged, setTokens } from '@/api/client'
import type { ProfilePatch, User } from '@/types'
import { detectHourCycle } from '@/utils/timeOfDay'

// Where the 12/24 choice lived before it moved to the profile.
const LEGACY_HOUR_CYCLE_KEY = 'hourtime.hourCycle'

function takeLegacyHourCycle(): 12 | 24 | null {
  try {
    const raw = localStorage.getItem(LEGACY_HOUR_CYCLE_KEY)
    localStorage.removeItem(LEGACY_HOUR_CYCLE_KEY)
    return raw === '12' ? 12 : raw === '24' ? 24 : null
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  /** False until the stored session has been checked, so guards do not bounce. */
  const restored = ref(false)

  const isAuthenticated = computed(() => user.value !== null)

  // A refresh that fails clears the tokens from under us; follow it.
  onTokensChanged((tokens) => {
    if (!tokens) user.value = null
  })

  /**
   * A profile without a time zone has never met a client: take the zone and
   * the 12/24 habit from the first browser that signs in. Best effort - if it
   * fails, the next load tries again.
   */
  async function fillDeviceDefaults(): Promise<void> {
    if (!user.value || user.value.timezone !== null) return
    const hourCycle = takeLegacyHourCycle() ?? (detectHourCycle() === '12' ? 12 : 24)
    try {
      user.value = await authApi.updateMe({
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        hour_cycle: hourCycle,
      })
    } catch {
      // Stays unset until the next load; nothing on screen depends on it.
    }
  }

  function adopt(next: User): void {
    user.value = next
    void fillDeviceDefaults()
  }

  async function restore(): Promise<void> {
    if (restored.value) return
    if (getTokens()) {
      try {
        adopt(await authApi.me())
      } catch {
        setTokens(null)
      }
    }
    restored.value = true
  }

  async function signIn(email: string, password: string): Promise<void> {
    const result = await authApi.login(email, password)
    setTokens(result.tokens)
    adopt(result.user)
    restored.value = true
  }

  async function signUp(email: string, password: string): Promise<void> {
    await authApi.register(email, password)
    await signIn(email, password)
  }

  /** Applied at once so the control does not lag; rolled back if the server refuses. */
  async function updateProfile(patch: ProfilePatch): Promise<void> {
    const before = user.value
    if (!before) return
    user.value = { ...before, ...patch }
    try {
      user.value = await authApi.updateMe(patch)
    } catch (error) {
      if (user.value) user.value = before
      throw error
    }
  }

  async function signOut(): Promise<void> {
    try {
      await authApi.logout()
    } catch {
      // Already invalid server-side; drop it locally regardless.
    } finally {
      setTokens(null)
      user.value = null
    }
  }

  async function signOutEverywhere(): Promise<void> {
    try {
      await authApi.logoutEverywhere()
    } finally {
      setTokens(null)
      user.value = null
    }
  }

  return {
    user,
    restored,
    isAuthenticated,
    restore,
    signIn,
    signUp,
    updateProfile,
    signOut,
    signOutEverywhere,
  }
})
