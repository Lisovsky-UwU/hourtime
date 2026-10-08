import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { useProjectsStore } from '@/stores/projects'
import { useTimerStore } from '@/stores/timer'
import { useWorkspaceStore } from '@/stores/workspace'
import type { TimeEntry } from '@/types'
import { amountCents, currencySymbol, formatMoney, toCents } from '@/utils/money'

export interface BillableTotals {
  /** Billable time, ticking along with a running billable entry. */
  seconds: number
  /** Sum of the entries that have a rate. */
  cents: number
  /** False when no billable entry has a rate: then there is no sum to show, not a zero. */
  priced: boolean
}

/**
 * Billable time and money worked out in the browser from the current rates.
 *
 * Amounts are never stored on the server either, so a changed rate shows up
 * here at once without reloading the entries.
 */
export function useBilling() {
  const { locale } = useI18n()
  const workspace = useWorkspaceStore()
  const projects = useProjectsStore()
  const timer = useTimerStore()

  /** The project's own rate wins; without one the workspace default applies. */
  function rateCentsOf(entry: TimeEntry): number | null {
    const own = toCents(projects.find(entry.project_id)?.hourly_rate ?? null)
    return own ?? workspace.defaultRateCents
  }

  function totals(items: TimeEntry[]): BillableTotals {
    const result: BillableTotals = { seconds: 0, cents: 0, priced: false }
    for (const entry of items) {
      if (!entry.billable) continue
      const seconds = timer.secondsOf(entry)
      result.seconds += seconds
      const rate = rateCentsOf(entry)
      if (rate === null) continue
      result.cents += amountCents(seconds, rate)
      result.priced = true
    }
    return result
  }

  const symbol = computed(() => currencySymbol(workspace.currency, locale.value))

  function money(cents: number): string {
    return formatMoney(cents, workspace.currency, locale.value)
  }

  return { totals, money, symbol }
}
