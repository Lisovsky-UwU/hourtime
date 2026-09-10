<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import { useAsyncAction } from '@/composables/useApiError'
import { currentLocale, setLocale, SUPPORTED_LOCALES } from '@/i18n'
import type { Locale } from '@/i18n'
import { useAuthStore } from '@/stores/auth'
import { useEntriesStore } from '@/stores/entries'
import { useProjectsStore } from '@/stores/projects'
import { useTimerStore } from '@/stores/timer'

/** Language names stay in their own language — those are never translated. */
const LOCALE_NAMES: Record<Locale, string> = { en: 'English' }

const { t } = useI18n()
const auth = useAuthStore()
const timer = useTimerStore()
const projects = useProjectsStore()
const entries = useEntriesStore()
const router = useRouter()
const { busy, error, run } = useAsyncAction()

const locale = ref<Locale>(currentLocale())

async function changeLocale(event: Event) {
  const value = (event.target as HTMLSelectElement).value as Locale
  await setLocale(value)
  locale.value = value
}

async function signOutEverywhere() {
  const done = await run(async () => {
    await auth.signOutEverywhere()
    return true
  })
  if (!done) return
  timer.reset()
  projects.reset()
  entries.reset()
  await router.replace({ name: 'login' })
}
</script>

<template>
  <div class="page stack">
    <h1>{{ t('settings.title') }}</h1>

    <section class="card section stack">
      <div>
        <h2>{{ t('settings.language') }}</h2>
        <p class="muted small">{{ t('settings.languageHint') }}</p>
      </div>
      <select :value="locale" :aria-label="t('settings.language')" @change="changeLocale">
        <option v-for="code in SUPPORTED_LOCALES" :key="code" :value="code">
          {{ LOCALE_NAMES[code] }}
        </option>
      </select>
    </section>

    <section class="card section stack">
      <div>
        <h2>{{ t('settings.account') }}</h2>
        <p class="muted small">{{ t('settings.signedInAs', { email: auth.user?.email ?? '' }) }}</p>
      </div>

      <div>
        <h2 class="sub">{{ t('settings.sessions') }}</h2>
        <p class="muted small">{{ t('settings.signOutEverywhereHint') }}</p>
      </div>

      <p v-if="error" class="banner">{{ error }}</p>

      <div>
        <button type="button" class="btn-danger" :disabled="busy" @click="signOutEverywhere">
          {{ t('settings.signOutEverywhere') }}
        </button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.section {
  padding: 18px;
  gap: 12px;
}

.section h2 {
  font-size: 1rem;
}

.sub {
  margin-top: 4px;
}

select {
  max-width: 220px;
}
</style>
