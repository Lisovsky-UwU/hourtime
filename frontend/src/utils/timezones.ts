/** IANA time zones for the profile picker. */

export interface TimezoneOption {
  value: string
  /** `Europe/Moscow (UTC+03:00)`: searchable by place and by offset. */
  label: string
}

/** `UTC+03:00` for `Europe/Moscow` right now; DST makes it change over the year. */
function currentOffset(zone: string, at: Date): string {
  try {
    const part = new Intl.DateTimeFormat('en-US', { timeZone: zone, timeZoneName: 'longOffset' })
      .formatToParts(at)
      .find((item) => item.type === 'timeZoneName')
    return (part?.value ?? 'GMT').replace('GMT', 'UTC')
  } catch {
    // A zone the server knows but this browser does not: name it without an offset.
    return '?'
  }
}

export function deviceTimezone(): string {
  return Intl.DateTimeFormat().resolvedOptions().timeZone
}

export function timezoneLabel(zone: string, at = new Date()): string {
  return `${zone.replaceAll('_', ' ')} (${currentOffset(zone, at)})`
}

/**
 * Every zone the browser knows, plus `extra` - the stored zone may be an alias
 * (`Europe/Kiev`) that the browser lists under its new name.
 */
export function timezoneOptions(extra: (string | null)[] = []): TimezoneOption[] {
  const zones = new Set(Intl.supportedValuesOf('timeZone'))
  zones.add('UTC')
  for (const zone of extra) if (zone) zones.add(zone)
  const now = new Date()
  return [...zones]
    .sort((a, b) => a.localeCompare(b))
    .map((zone) => ({ value: zone, label: timezoneLabel(zone, now) }))
}
