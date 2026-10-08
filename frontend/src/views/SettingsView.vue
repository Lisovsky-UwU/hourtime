<script setup lang="ts">
import { computed, ref, useId, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import type { IconName } from '@/components/AppIcon.vue'
import ChangePasswordDialog from '@/components/ChangePasswordDialog.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiCombobox from '@/components/ui/UiCombobox.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiSegmented from '@/components/ui/UiSegmented.vue'
import { toast } from '@/components/ui/toast'
import { messageFor, useAsyncAction } from '@/composables/useApiError'
import { currentLocale, LOCALE_NAMES, setLocale, SUPPORTED_LOCALES } from '@/i18n'
import type { Locale } from '@/i18n'
import { useAuthStore } from '@/stores/auth'
import { useEntriesStore } from '@/stores/entries'
import type { Theme } from '@/stores/preferences'
import { usePreferencesStore } from '@/stores/preferences'
import { useProjectsStore } from '@/stores/projects'
import { useTimerStore } from '@/stores/timer'
import type { DurationFormat, ProfilePatch } from '@/types'
import { formatDuration } from '@/utils/duration'
import type { HourCycle } from '@/utils/timeOfDay'
import { deviceTimezone, timezoneLabel, timezoneOptions } from '@/utils/timezones'

const { t, locale: i18nLocale } = useI18n()
const auth = useAuthStore()
const preferences = usePreferencesStore()
const timer = useTimerStore()
const projects = useProjectsStore()
const entries = useEntriesStore()
const router = useRouter()
const { busy, error, run } = useAsyncAction()
const nameErrorId = useId()

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

// Monday first in both languages; the names come from Intl, so no translations.
const WEEK_ORDER = [1, 2, 3, 4, 5, 6, 0]
const weekDays = computed(() => {
  const format = new Intl.DateTimeFormat(i18nLocale.value, { weekday: 'short' })
  // 2026-01-04 was a Sunday, so day N of that week is getDay() === N.
  return WEEK_ORDER.map((day) => ({
    value: String(day),
    label: format.format(new Date(2026, 0, 4 + day)),
  }))
})

// One hour five minutes: every format writes it differently.
const SAMPLE_SECONDS = 3900
const durationFormats = computed(() =>
  (['classic', 'decimal', 'improved'] as DurationFormat[]).map((value) => ({
    value,
    label: formatDuration(SAMPLE_SECONDS, value, i18nLocale.value),
  })),
)

// Language names stay in their own language: a lost user looks for "Русский".
const locales = SUPPORTED_LOCALES.map((value) => ({ value, label: LOCALE_NAMES[value] }))

const locale = ref<Locale>(currentLocale())
const confirmSignOut = ref(false)
const changingPassword = ref(false)

async function changeLocale(value: Locale) {
  await setLocale(value)
  locale.value = value
}

/** Profile settings save as soon as they change; a refusal rolls the control back. */
async function save(patch: ProfilePatch): Promise<boolean> {
  try {
    await auth.updateProfile(patch)
    return true
  } catch (cause) {
    toast.error(t('settings.saveFailed'), messageFor(cause))
    return false
  }
}

const hourCycle = computed({
  get: () => preferences.hourCycle,
  set: (value: HourCycle) => void save({ hour_cycle: value === '12' ? 12 : 24 }),
})

const weekStart = computed({
  get: () => String(preferences.weekStart),
  set: (value: string) => void save({ week_start: Number(value) }),
})

const durationFormat = computed({
  get: () => preferences.durationFormat,
  set: (value: DurationFormat) => void save({ duration_format: value }),
})

// --- name: saved on blur or Enter, like the fields of a time entry ----------

const displayName = ref('')
const nameError = ref<string | null>(null)

watch(
  () => auth.user?.display_name,
  (value) => {
    displayName.value = value ?? ''
  },
  { immediate: true },
)

async function saveName() {
  const value = displayName.value.trim() || null
  if (value === (auth.user?.display_name ?? null)) return
  nameError.value = null
  try {
    await auth.updateProfile({ display_name: value })
  } catch (cause) {
    nameError.value = messageFor(cause)
  }
}

// --- time zone ---------------------------------------------------------------

const device = deviceTimezone()
const timezones = computed(() => timezoneOptions([auth.user?.timezone ?? null, device]))

const timezone = computed({
  get: () => auth.user?.timezone ?? null,
  set: (value: string | null) => {
    if (value) void save({ timezone: value })
  },
})

const showDeviceZone = computed(() => !!auth.user?.timezone && auth.user.timezone !== device)

// --- sessions ----------------------------------------------------------------

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
      <header class="section-head">
        <h2>{{ t('settings.profile') }}</h2>
        <p class="muted scope">{{ t('settings.synced') }}</p>
      </header>

      <div class="setting">
        <div class="setting-text">
          <h3>{{ t('settings.displayName') }}</h3>
          <p class="muted">{{ t('settings.displayNameHint') }}</p>
          <p v-if="nameError" :id="nameErrorId" class="error" role="alert">{{ nameError }}</p>
        </div>
        <UiInput
          v-model="displayName"
          class="control-wide"
          maxlength="100"
          autocomplete="name"
          :aria-label="t('settings.displayName')"
          :placeholder="auth.user?.email"
          :invalid="!!nameError"
          :aria-describedby="nameError ? nameErrorId : undefined"
          @change="saveName"
          @keydown.enter="saveName"
        />
      </div>

      <div class="setting">
        <div class="setting-text">
          <h3>{{ t('settings.timezone') }}</h3>
          <p class="muted">{{ t('settings.timezoneHint') }}</p>
          <p v-if="showDeviceZone" class="muted device-zone">
            {{ t('settings.deviceZone', { zone: timezoneLabel(device) }) }}
            <UiButton variant="ghost" size="sm" @click="timezone = device">
              {{ t('settings.useDeviceZone') }}
            </UiButton>
          </p>
        </div>
        <div class="control-wide picker">
          <UiCombobox
            v-model="timezone"
            :items="timezones"
            :label="t('settings.timezone')"
            :placeholder="t('settings.timezoneUnset')"
          />
        </div>
      </div>
    </section>

    <section class="section">
      <header class="section-head">
        <h2>{{ t('settings.tracking') }}</h2>
        <p class="muted scope">{{ t('settings.synced') }}</p>
      </header>

      <div class="setting">
        <div class="setting-text">
          <h3>{{ t('settings.weekStart') }}</h3>
          <p class="muted">{{ t('settings.weekStartHint') }}</p>
        </div>
        <UiSegmented v-model="weekStart" :options="weekDays" :label="t('settings.weekStart')" />
      </div>

      <div class="setting">
        <div class="setting-text">
          <h3>{{ t('settings.durationFormat') }}</h3>
          <p class="muted">{{ t('settings.durationFormatHint') }}</p>
        </div>
        <UiSegmented
          v-model="durationFormat"
          :options="durationFormats"
          :label="t('settings.durationFormat')"
          numeric
        />
      </div>

      <div class="setting">
        <div class="setting-text">
          <h3>{{ t('settings.timeFormat') }}</h3>
          <p class="muted">{{ t('settings.timeFormatHint') }}</p>
        </div>
        <UiSegmented v-model="hourCycle" :options="hourCycles" :label="t('settings.timeFormat')" />
      </div>
    </section>

    <section class="section">
      <header class="section-head">
        <h2>{{ t('settings.appearance') }}</h2>
        <p class="muted scope">{{ t('settings.local') }}</p>
      </header>

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
    </section>

    <section class="section">
      <header class="section-head">
        <h2>{{ t('settings.account') }}</h2>
      </header>

      <div class="setting">
        <div class="setting-text">
          <h3>{{ t('settings.email') }}</h3>
          <p class="muted">{{ auth.user?.email }}</p>
        </div>
      </div>

      <div class="setting">
        <div class="setting-text">
          <h3>{{ t('settings.password') }}</h3>
          <p class="muted">{{ t('settings.passwordChangeHint') }}</p>
        </div>
        <UiButton icon="key" @click="changingPassword = true">
          {{ t('settings.changePassword') }}
        </UiButton>
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

    <ChangePasswordDialog :open="changingPassword" @close="changingPassword = false" />

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

.section-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 4px 16px;
  flex-wrap: wrap;
  padding: 14px 20px 12px;
  border-bottom: 1px solid var(--border);
}

.section-head h2 {
  font-size: var(--text-md);
}

/* Says where the values live: on the server for every device, or in this browser. */
.scope {
  font-size: var(--text-xs);
}

.setting {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px 24px;
  padding: 16px 20px;
  border-top: 1px solid var(--border);
}

.section-head + .setting {
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

.control-wide {
  flex: 0 1 280px;
  min-width: 0;
}

/* A settings field, not a chip in a dense row: give the trigger a frame. */
.picker :deep(.ui-combobox-trigger) {
  width: 100%;
  justify-content: space-between;
  border-color: var(--control-border);
  background: var(--surface);
}

.device-zone {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 2px 8px;
  margin-top: 4px;
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

  .control-wide {
    flex-basis: auto;
    width: 100%;
  }

  .section-head {
    padding-inline: 16px;
  }
}
</style>
