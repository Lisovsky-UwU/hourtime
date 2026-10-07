/**
 * Localisation setup.
 *
 * English is the only language shipped today, but every string already goes
 * through `t()` and locales load on demand — adding one is dropping a JSON file
 * into `src/locales` and listing it in SUPPORTED_LOCALES.
 */

import { createI18n } from 'vue-i18n'

import en from '@/locales/en.json'

export const SUPPORTED_LOCALES = ['en'] as const
export type Locale = (typeof SUPPORTED_LOCALES)[number]

export const DEFAULT_LOCALE: Locale = 'en'
const STORAGE_KEY = 'hourtime.locale'

/** Dates and numbers are formatted through i18n too, never with ad-hoc calls. */
const datetimeFormats = {
  en: {
    time: { hour: '2-digit', minute: '2-digit' },
    date: { year: 'numeric', month: 'short', day: 'numeric' },
    weekday: { weekday: 'long', month: 'short', day: 'numeric' },
    weekdayYear: { weekday: 'long', month: 'short', day: 'numeric', year: 'numeric' },
    dayShort: { weekday: 'short', month: 'short', day: 'numeric' },
  },
} as const

function isSupported(value: string | null): value is Locale {
  return value !== null && (SUPPORTED_LOCALES as readonly string[]).includes(value)
}

function preferredLocale(): Locale {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (isSupported(stored)) return stored
  } catch {
    // Storage unavailable — fall through to the browser's preference.
  }
  const fromBrowser = navigator.languages.map((tag) => tag.split('-')[0] ?? '')
  return fromBrowser.find(isSupported) ?? DEFAULT_LOCALE
}

export const i18n = createI18n({
  legacy: false,
  locale: preferredLocale(),
  fallbackLocale: DEFAULT_LOCALE,
  messages: { en },
  datetimeFormats,
})

export function currentLocale(): Locale {
  return i18n.global.locale.value as Locale
}

export async function setLocale(locale: Locale): Promise<void> {
  if (!i18n.global.availableLocales.includes(locale)) {
    const loaded = await import(`../locales/${locale}.json`)
    i18n.global.setLocaleMessage(locale, loaded.default)
  }
  i18n.global.locale.value = locale
  document.documentElement.lang = locale
  try {
    localStorage.setItem(STORAGE_KEY, locale)
  } catch {
    // The choice just will not survive a reload.
  }
}

export function applyInitialLocale(): void {
  document.documentElement.lang = currentLocale()
}
