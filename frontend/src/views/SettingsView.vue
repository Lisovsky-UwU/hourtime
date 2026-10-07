<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import type { IconName } from '@/components/AppIcon.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiSegmented from '@/components/ui/UiSegmented.vue'
import { useAsyncAction } from '@/composables/useApiError'
import { currentLocale, LOCALE_NAMES, setLocale, SUPPORTED_LOCALES } from '@/i18n'
import type { Locale } from '@/i18n'
import { useAuthStore } from '@/stores/auth'
import { useEntriesStore } from '@/stores/entries'
import type { Theme } from '@/stores/preferences'
import { usePreferencesStore } from '@/stores/preferences'
import { useProjectsStore } from '@/stores/projects'
import { useTimerStore } from '@/stores/timer'
import type { HourCycle } from '@/utils/timeOfDay'

const { t } = useI18n()
const auth = useAuthStore()
const preferences = usePreferencesStore()
const timer = useTimerStore()
const projects = useProjectsStore()
const entries = useEntriesStore()
const router = useRouter()
const { busy, error, run } = useAsyncAction()

const THEME_ICONS: Record<Theme, IconName> = {
  auto: 'theme-auto',
  light: 'theme-light',
  dark: 'theme-dark',
}

const themes = computed(() =>
  (['auto', 'light', 'dark'] as const).map((value) => ({
    value,
    label: t(`settings.theme.${value}`),
    icon: THEME_ICONS[value],
  })),
)

const hourCycles = computed(() =>
  (['24', '12'] as HourCycle[]).map((value) => ({ value, label: t(`settings.hourCycle.${value}`) })),
)

// Language names stay in their own language: a lost user looks for "Русский".
const locales = SUPPORTED_LOCALES.map((value) => ({ value, label: LOCALE_NAMES[value] }))

const locale = ref<Locale>(currentLocale())
const confirmSignOut = ref(false)

async function changeLocale(value: Locale) {
  await setLocale(value)
  locale.value = value
}

async function signOutEverywhere() {
  const done = await run(async () => {
    await auth.signOutEverywhere()
    return true
  })
  confirmSignOut.value = false
  if (!done) return
  timer.reset()
  projects.reset()
  entries.reset()
  await router.replace({ name: 'login' })
}
</script>

<template>
  <div class="page settings">
    <h1>{{ t('settings.title') }}</h1>

    <section class="section">
      <h2>{{ t('settings.appearance') }}</h2>

      <div class="setting">
        <div class="setting-text">
          <h3>{{ t('settings.themeLabel') }}</h3>
          <p class="muted">{{ t('settings.themeHint') }}</p>
        </div>
        <UiSegmented v-model="preferences.theme" :options="themes" :label="t('settings.themeLabel')" />
      </div>

      <div class="setting">
        <div class="setting-text">
          <h3>{{ t('settings.language') }}</h3>
          <p class="muted">{{ t('settings.languageHint') }}</p>
        </div>
        <UiSegmented
          :model-value="locale"
          :options="locales"
          :label="t('settings.language')"
          @update:model-value="changeLocale"
        />
      </div>

      <div class="setting">
        <div class="setting-text">
          <h3>{{ t('settings.timeFormat') }}</h3>
          <p class="muted">{{ t('settings.timeFormatHint') }}</p>
        </div>
        <UiSegmented
          v-model="preferences.hourCycle"
          :options="hourCycles"
          :label="t('settings.timeFormat')"
        />
      </div>
    </section>

    <section class="section">
      <h2>{{ t('settings.account') }}</h2>

      <div class="setting">
        <div class="setting-text">
          <h3>{{ t('settings.email') }}</h3>
          <p class="muted">{{ auth.user?.email }}</p>
        </div>
      </div>

      <div class="setting">
        <div class="setting-text">
          <h3>{{ t('settings.sessions') }}</h3>
          <p class="muted">{{ t('settings.signOutEverywhereHint') }}</p>
          <p v-if="error" class="error" role="alert">{{ error }}</p>
        </div>
        <UiButton variant="danger" icon="sign-out" :disabled="busy" @click="confirmSignOut = true">
          {{ t('settings.signOutEverywhere') }}
        </UiButton>
      </div>
    </section>

    <ConfirmDialog
      :open="confirmSignOut"
      :title="t('settings.signOutEverywhereTitle')"
      :message="t('settings.signOutEverywhereHint')"
      :confirm-label="t('settings.signOutEverywhere')"
      :busy="busy"
      @close="confirmSignOut = false"
      @confirm="signOutEverywhere"
    />
  </div>
</template>

<style scoped>
.settings {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 760px;
  padding-top: 28px;
}

.section {
  border: 1px solid var(--border);
  border-radius: var(--radius-sheet);
  background: var(--surface);
}

.section h2 {
  padding: 14px 20px 12px;
  border-bottom: 1px solid var(--border);
  font-size: var(--text-md);
}

.setting {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px 24px;
  padding: 16px 20px;
  border-top: 1px solid var(--border);
}

.section h2 + .setting {
  border-top: none;
}

.setting-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  max-width: 52ch;
}

.setting-text h3 {
  font-size: var(--text-sm);
  font-weight: 500;
}

.error {
  margin-top: 6px;
  color: var(--danger);
}

@media (width < 600px) {
  .settings {
    padding-top: 16px;
  }

  .setting {
    flex-direction: column;
    align-items: flex-start;
    padding: 14px 16px;
  }

  .section h2 {
    padding-inline: 16px;
  }
}
</style>
