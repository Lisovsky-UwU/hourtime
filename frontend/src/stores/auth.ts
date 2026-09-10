import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import * as authApi from '@/api/auth'
import { getTokens, onTokensChanged, setTokens } from '@/api/client'
import type { User } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  /** False until the stored session has been checked, so guards do not bounce. */
  const restored = ref(false)

  const isAuthenticated = computed(() => user.value !== null)

  // A refresh that fails clears the tokens from under us; follow it.
  onTokensChanged((tokens) => {
    if (!tokens) user.value = null
  })

  async function restore(): Promise<void> {
    if (restored.value) return
    if (getTokens()) {
      try {
        user.value = await authApi.me()
      } catch {
        setTokens(null)
      }
    }
    restored.value = true
  }

  async function signIn(email: string, password: string): Promise<void> {
    const result = await authApi.login(email, password)
    setTokens(result.tokens)
    user.value = result.user
    restored.value = true
  }

  async function signUp(email: string, password: string): Promise<void> {
    await authApi.register(email, password)
    await signIn(email, password)
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

  return { user, restored, isAuthenticated, restore, signIn, signUp, signOut, signOutEverywhere }
})
