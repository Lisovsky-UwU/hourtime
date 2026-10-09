/**
 * Localisation setup.
 *
 * English ships in the main bundle; other locales load on demand. Adding one
 * is a JSON file in `src/locales`, an entry in SUPPORTED_LOCALES and
 * LOCALE_NAMES, its datetime formats and, if its plurals differ from English,
 * a plural rule.
 */

import { createI18n } from 'vue-i18n'

import en from '@/locales/en.json'

export const SUPPORTED_LOCALES = ['en', 'ru'] as const
export type Locale = (typeof SUPPORTED_LOCALES)[number]

/** Each language named in itself: someone lost in a foreign UI looks for their own word. */
export const LOCALE_NAMES: Record<Locale, string> = { en: 'English', ru: 'Русский' }

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
    axisDay: { day: 'numeric' },
    axisWeekday: { weekday: 'short', day: 'numeric' },
    axisMonth: { month: 'short' },
    month: { month: 'long', year: 'numeric' },
  },
  ru: {
    time: { hour: '2-digit', minute: '2-digit' },
    date: { year: 'numeric', month: 'short', day: 'numeric' },
    weekday: { weekday: 'long', day: 'numeric', month: 'long' },
    weekdayYear: { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' },
    dayShort: { weekday: 'short', day: 'numeric', month: 'short' },
    axisDay: { day: 'numeric' },
    axisWeekday: { weekday: 'short', day: 'numeric' },
    axisMonth: { month: 'short' },
    month: { month: 'long', year: 'numeric' },
  },
} as const

/**
 * Russian has three plural forms: 1 запись, 2 записи, 5 записей (and 21
 * запись, 11 записей). Messages list them in that order.
 */
function russianPlural(choice: number, choicesLength: number): number {
  if (choicesLength < 3) return choice === 1 ? 0 : 1
  const mod10 = choice % 10
  const mod100 = choice % 100
  if (mod10 === 1 && mod100 !== 11) return 0
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return 1
  return 2
}

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

// Starts in English; installInitialLocale() switches before the app mounts.
export const i18n = createI18n({
  legacy: false,
  locale: DEFAULT_LOCALE,
  fallbackLocale: DEFAULT_LOCALE,
  messages: { en },
  datetimeFormats,
  pluralRules: { ru: russianPlural },
})

export function currentLocale(): Locale {
  return i18n.global.locale.value as Locale
}

async function loadMessages(locale: Locale): Promise<void> {
  if (i18n.global.availableLocales.includes(locale)) return
  const loaded = await import(`../locales/${locale}.json`)
  i18n.global.setLocaleMessage(locale, loaded.default)
}

function apply(locale: Locale): void {
  i18n.global.locale.value = locale
  document.documentElement.lang = locale
}

export async function setLocale(locale: Locale): Promise<void> {
  await loadMessages(locale)
  apply(locale)
  try {
    localStorage.setItem(STORAGE_KEY, locale)
  } catch {
    // The choice just will not survive a reload.
  }
}

/**
 * Loads the stored or browser language before the first render, so a Russian
 * browser never sees English first. The choice is not stored: until the user
 * picks a language, the browser keeps deciding.
 */
export async function installInitialLocale(): Promise<void> {
  const locale = preferredLocale()
  try {
    await loadMessages(locale)
    apply(locale)
  } catch {
    apply(DEFAULT_LOCALE)
  }
}
