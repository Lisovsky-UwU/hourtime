/**
 * Rates and amounts, kept in integer cents so sums never pick up float noise.
 *
 * Mirrors `domain/billing.py` on the server: each entry is rounded half up to
 * the cent, totals add up the rounded amounts. Keep the two in step.
 */

/** `"150.00"` from the API to 15000; null stays null. */
export function toCents(rate: string | null): number | null {
  if (rate === null) return null
  const [whole = '0', fraction = ''] = rate.split('.')
  return Number(whole) * 100 + Number(fraction.padEnd(2, '0').slice(0, 2))
}

/** Worth of `seconds` at an hourly rate. Math.round is half up for these positive values. */
export function amountCents(seconds: number, rateCents: number): number {
  return Math.round((Math.floor(seconds) * rateCents) / 3600)
}

export function formatMoney(cents: number, currency: string, locale: string): string {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
    currencyDisplay: 'narrowSymbol',
  }).format(cents / 100)
}

/** `₽` for RUB, `$` for USD; currencies without a symbol come back as their code. */
export function currencySymbol(currency: string, locale: string): string {
  const part = new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
    currencyDisplay: 'narrowSymbol',
  })
    .formatToParts(0)
    .find((item) => item.type === 'currency')
  return part?.value ?? currency
}

/** A rate as typed: `1500`, `1 500,5`, `1500.50`. Empty is null, garbage is undefined. */
export function parseRate(input: string): string | null | undefined {
  const text = input.replace(/[\s\u00a0\u202f]/g, '').replace(',', '.')
  if (text === '') return null
  if (!/^\d{1,10}(\.\d{1,2})?$/.test(text)) return undefined
  return text
}

/** A stored rate for an input field, in the locale's own notation and without grouping. */
export function rateForInput(rate: string | null, locale: string): string {
  if (rate === null) return ''
  return new Intl.NumberFormat(locale, {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
    useGrouping: false,
  }).format(Number(rate))
}

export interface CurrencyOption {
  value: string
  /** `RUB - Russian ruble`: searchable by code and by name. */
  label: string
}

export function currencyOptions(locale: string, extra: string | null = null): CurrencyOption[] {
  const codes = new Set(Intl.supportedValuesOf('currency'))
  if (extra) codes.add(extra)
  const names = new Intl.DisplayNames([locale], { type: 'currency' })
  return [...codes].sort().map((code) => ({ value: code, label: `${code} - ${names.of(code) ?? code}` }))
}
