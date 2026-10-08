<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import ConfirmDialog from '@/components/ConfirmDialog.vue'
import EntryGroup from '@/components/EntryGroup.vue'
import EntryRow from '@/components/EntryRow.vue'
import TimerBar from '@/components/TimerBar.vue'
import UiButton from '@/components/ui/UiButton.vue'
import { toast } from '@/components/ui/toast'
import { messageFor } from '@/composables/useApiError'
import type { BillableTotals } from '@/composables/useBilling'
import { useBilling } from '@/composables/useBilling'
import { useDuration } from '@/composables/useDuration'
import { useClientsStore } from '@/stores/clients'
import { useEntriesStore } from '@/stores/entries'
import { usePreferencesStore } from '@/stores/preferences'
import { useProjectsStore } from '@/stores/projects'
import { useTagsStore } from '@/stores/tags'
import { useTimerStore } from '@/stores/timer'
import { useWorkspaceStore } from '@/stores/workspace'
import type { TimeEntry } from '@/types'
import { localDayKey, startOfLocalDay, startOfLocalWeek } from '@/utils/datetime'
import { secondsBetween } from '@/utils/duration'
import { serverNow } from '@/utils/serverTime'

const HOUR_MS = 60 * 60 * 1000

const { t, d } = useI18n()
const timer = useTimerStore()
const showDuration = useDuration()
const entries = useEntriesStore()
const preferences = usePreferencesStore()
const projects = useProjectsStore()
const clients = useClientsStore()
const tags = useTagsStore()
const workspace = useWorkspaceStore()
const billing = useBilling()
const initialLoad = ref(true)
/** Only a failed load of the list shows inline; failed actions go to a toast. */
const loadError = ref<string | null>(null)
const busy = ref(false)

async function act(action: () => Promise<unknown>): Promise<boolean> {
  busy.value = true
  try {
    await action()
    return true
  } catch (cause) {
    toast.error(messageFor(cause))
    return false
  } finally {
    busy.value = false
  }
}

const currentYear = new Date().getFullYear()
const todayKey = localDayKey(startOfLocalDay().toISOString())
const yesterdayKey = localDayKey(startOfLocalDay(-1).toISOString())

/** One line of a day: a single entry, or several alike folded together. */
interface DayRow {
  key: string
  entries: TimeEntry[]
}

interface DayGroup {
  key: string
  label: string
  totalSeconds: number
  billable: BillableTotals
  rows: DayRow[]
}

/**
 * Same description, project, tags and billable flag within a day make one row, placed where the
 * newest of them is. The running entry is never folded away: it is the one
 * row that has to stay in sight.
 */
function foldAlike(items: TimeEntry[]): DayRow[] {
  const rows: DayRow[] = []
  const byKey = new Map<string, DayRow>()
  for (const entry of items) {
    if (entry.stopped_at === null) {
      rows.push({ key: entry.id, entries: [entry] })
      continue
    }
    const tagKey = [...entry.tag_ids].sort().join(',')
    const key = `alike:${entry.description}\u0000${entry.project_id ?? ''}\u0000${tagKey}\u0000${entry.billable}`
    const row = byKey.get(key)
    if (row) {
      row.entries.push(entry)
      continue
    }
    const created = { key, entries: [entry] }
    byKey.set(key, created)
    rows.push(created)
  }
  return rows
}

/** The list is flat on the server; the day headings are purely presentational. */
const groups = computed<DayGroup[]>(() => {
  const buckets = new Map<string, TimeEntry[]>()
  for (const entry of entries.items) {
    const key = localDayKey(entry.started_at)
    const bucket = buckets.get(key)
    if (bucket) bucket.push(entry)
    else buckets.set(key, [entry])
  }

  return [...buckets.entries()].map(([key, items]) => ({
    key,
    label: labelFor(key, items[0]),
    totalSeconds: items.reduce((sum, item) => sum + timer.secondsOf(item), 0),
    billable: billing.totals(items),
    rows: foldAlike(items),
  }))
})

/**
 * Counted from the loaded entries only: a long week can reach past the first
 * page. Server-side totals arrive with reports (stage 9 of the plan).
 */
const weekEntries = computed(() => {
  const from = startOfLocalWeek(preferences.weekStart).getTime()
  return entries.items.filter((item) => Date.parse(item.started_at) >= from)
})

const weekTotal = computed(() =>
  weekEntries.value.reduce((sum, item) => sum + timer.secondsOf(item), 0),
)

const weekBillable = computed(() => billing.totals(weekEntries.value))

/** Newest first: if the oldest loaded entry is still inside the week, more may follow. */
const weekPartial = computed(() => {
  const oldest = entries.items.at(-1)
  return entries.hasMore && !!oldest && Date.parse(oldest.started_at) >= startOfLocalWeek(preferences.weekStart).getTime()
})

function labelFor(key: string, sample: TimeEntry | undefined): string {
  if (!sample) return key
  const date = new Date(sample.started_at)
  if (key === todayKey) return `${t('entries.today')}, ${d(date, 'dayShort')}`
  if (key === yesterdayKey) return `${t('entries.yesterday')}, ${d(date, 'dayShort')}`
  return d(date, date.getFullYear() === currentYear ? 'weekday' : 'weekdayYear')
}

/**
 * Adds a finished entry covering the last hour, ready to be adjusted in place.
 * There is no form to fill in first — the row itself is the form.
 */
async function addEntry() {
  const now = serverNow()
  await act(() =>
    entries.create({
      started_at: new Date(now - HOUR_MS).toISOString(),
      stopped_at: new Date(now).toISOString(),
      description: '',
      project_id: null,
    }),
  )
}

/** An archived project cannot be assigned, so the copy goes without one. */
function usableProject(projectId: string | null): string | null {
  return projects.find(projectId)?.archived ? null : projectId
}

/** A tag deleted since the entry was loaded would be rejected. */
function usableTags(tagIds: string[]): string[] {
  return tagIds.filter((id) => tags.byId.has(id))
}

/**
 * Starts a new timer with the entry's description and project.
 *
 * The server stops a running timer itself, exactly where the new one starts,
 * so the stopped entry is folded into the list locally instead of refetched.
 */
async function continueEntry(entry: TimeEntry) {
  const previous = timer.entry
  await act(async () => {
    const started = await timer.start({
      description: entry.description,
      project_id: usableProject(entry.project_id),
      tag_ids: usableTags(entry.tag_ids),
      billable: entry.billable,
    })
    if (previous) {
      entries.upsert({
        ...previous,
        stopped_at: started.started_at,
        duration_seconds: secondsBetween(previous.started_at, started.started_at),
      })
    }
    entries.upsert(started)
  })
}

/** An exact copy, same times included, ready to be shifted in place. */
async function duplicateEntry(entry: TimeEntry) {
  if (!entry.stopped_at) return
  const stoppedAt = entry.stopped_at
  await act(() =>
    entries.create({
      started_at: entry.started_at,
      stopped_at: stoppedAt,
      description: entry.description,
      project_id: usableProject(entry.project_id),
      tag_ids: usableTags(entry.tag_ids),
      billable: entry.billable,
    }),
  )
}

const pendingDelete = ref<TimeEntry | null>(null)

async function removeEntry() {
  const entry = pendingDelete.value
  if (!entry) return
  const done = await act(async () => {
    await entries.remove(entry.id)
    if (timer.entry?.id === entry.id) timer.reset()
  })
  // On failure the dialog stays, so the user sees what they were doing.
  if (done) pendingDelete.value = null
}

async function loadMore() {
  try {
    await entries.loadMore()
  } catch (cause) {
    toast.error(messageFor(cause))
  }
}

/**
 * Another device may have started or stopped the timer while this tab idled.
 *
 * Returning to a tab fires `focus` and `visibilitychange` together, so the two
 * are collapsed into a single round instead of two identical pairs of requests.
 */
let pendingResync: number | null = null

function resync() {
  if (document.visibilityState !== 'visible' || pendingResync !== null) return
  pendingResync = window.setTimeout(() => {
    pendingResync = null
    void Promise.all([timer.sync(), entries.load()]).catch(() => {
      // A transient failure just leaves the last known state on screen.
    })
  }, 100)
}

async function loadAll() {
  loadError.value = null
  try {
    await Promise.all([projects.load(), clients.load(), tags.load(), workspace.load()])
    await Promise.all([timer.sync(), entries.load()])
  } catch (cause) {
    loadError.value = messageFor(cause)
  }
}

onMounted(async () => {
  await loadAll()
  initialLoad.value = false
  document.addEventListener('visibilitychange', resync)
  window.addEventListener('focus', resync)
})

onUnmounted(() => {
  if (pendingResync !== null) window.clearTimeout(pendingResync)
  document.removeEventListener('visibilitychange', resync)
  window.removeEventListener('focus', resync)
})
</script>

<template>
  <div class="timer-page">
    <div class="dock">
      <TimerBar />
    </div>

    <section class="entries" :aria-label="t('entries.title')">
      <header class="week">
        <h1>{{ t('entries.thisWeek') }}</h1>
        <span v-if="weekBillable.seconds > 0" class="week-billable muted">
          {{
            weekBillable.priced
              ? t('billing.weekSummaryPriced', {
                  time: showDuration(weekBillable.seconds),
                  amount: billing.money(weekBillable.cents),
                })
              : t('billing.weekSummary', { time: showDuration(weekBillable.seconds) })
          }}
        </span>
        <span
          class="week-total num"
          :title="weekPartial ? t('entries.weekPartial') : undefined"
        >
          {{ weekPartial ? '≥ ' : '' }}{{ showDuration(weekTotal) }}
        </span>
        <UiButton variant="ghost" size="sm" icon="plus" :disabled="busy" @click="addEntry">
          {{ t('entries.addManual') }}
        </UiButton>
      </header>

      <div v-if="loadError" class="alert" role="alert">
        <span>{{ t('entries.loadFailed') }} {{ loadError }}</span>
        <UiButton size="sm" @click="loadAll">{{ t('common.retry') }}</UiButton>
      </div>

      <div
        v-else-if="initialLoad && entries.loading"
        class="sheet"
        role="status"
        :aria-label="t('common.loading')"
      >
        <div v-for="n in 4" :key="n" class="skeleton-row">
          <span class="skeleton" aria-hidden="true" :style="{ width: `${30 + n * 9}%` }" />
          <span class="skeleton" aria-hidden="true" />
        </div>
      </div>

      <div v-else-if="!entries.items.length && !entries.loading" class="empty-state">
        <p class="empty-title">{{ t('entries.emptyTitle') }}</p>
        <p class="muted">{{ t('entries.empty') }}</p>
        <UiButton icon="plus" @click="addEntry">{{ t('entries.addManual') }}</UiButton>
      </div>

      <section v-for="group in groups" :key="group.key" class="sheet" :aria-label="group.label">
        <header class="day-head">
          <h2>{{ group.label }}</h2>
          <span
            v-if="group.billable.priced"
            class="day-amount num"
            :title="t('billing.billableTime', { time: showDuration(group.billable.seconds) })"
          >
            {{ billing.money(group.billable.cents) }}
          </span>
          <span class="day-total num">{{ showDuration(group.totalSeconds) }}</span>
        </header>

        <ul class="list">
          <template v-for="row in group.rows" :key="row.entries.length > 1 ? row.key : row.entries[0]!.id">
            <EntryGroup
              v-if="row.entries.length > 1"
              :entries="row.entries"
              @remove="pendingDelete = $event"
              @continue="continueEntry"
              @duplicate="duplicateEntry"
            />
            <EntryRow
              v-else
              :entry="row.entries[0]!"
              @remove="pendingDelete = $event"
              @continue="continueEntry"
              @duplicate="duplicateEntry"
            />
          </template>
        </ul>
      </section>

      <footer v-if="entries.items.length" class="more">
        <span class="muted">{{ t('entries.showing', entries.items.length) }}</span>
        <UiButton v-if="entries.hasMore" size="sm" :disabled="entries.loading" @click="loadMore">
          {{ entries.loading ? t('common.loading') : t('entries.loadMore') }}
        </UiButton>
      </footer>
    </section>

    <ConfirmDialog
      :open="pendingDelete !== null"
      :title="t('entries.deleteTitle')"
      :message="t('entries.deleteConfirm')"
      :confirm-label="t('entries.deleteAction')"
      :busy="busy"
      @close="pendingDelete = null"
      @confirm="removeEntry"
    />
  </div>
</template>

<style scoped>
.timer-page {
  max-width: 1040px;
  margin: 0 auto;
  padding: 0 24px 64px;
}

/* Sticky with the page color behind it, so rows scroll away under the bar
   instead of showing through above it. */
.dock {
  position: sticky;
  top: var(--topbar-h, 0px);
  z-index: 10;
  padding: 20px 0 16px;
  background: var(--bg);
}

.entries {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.week {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px 16px 0;
}

.week h1 {
  font-size: var(--text-lg);
}

/* Billable time and money: secondary to the week total, so in pencil and small. */
.week-billable {
  font-size: var(--text-xs);
  font-variant-numeric: tabular-nums;
}

.week-total {
  margin-left: auto;
  font-size: var(--text-lg);
  font-weight: 600;
}

.day-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 16px 10px;
  border-bottom: 1px solid var(--border);
}

.day-head h2 {
  flex: 1 1 auto;
  font-size: var(--text-md);
}

.day-amount {
  color: var(--text-muted);
  font-size: var(--text-sm);
}

/* Russian weekdays come lowercase from Intl ("вторник, 6 октября"). */
.day-head h2::first-letter {
  text-transform: uppercase;
}

/* Lines up with the duration column of the rows below: past the continue
   and menu columns and the gaps between them. */
.day-total {
  padding-right: 80px;
  font-size: var(--text-md);
  font-weight: 600;
}

.list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.skeleton-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 16px;
  border-top: 1px solid var(--border);
}

.skeleton-row:first-child {
  border-top: none;
}

.skeleton-row > .skeleton:last-child {
  width: 56px;
}

.more {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 0 16px;
  font-size: var(--text-xs);
}

@media (width < 768px) {
  .timer-page {
    padding: 0 12px 48px;
  }

  /* Two lines of bar under the top bar would eat a quarter of a phone
     screen; there the running timer already shows in the top bar. */
  .dock {
    position: static;
    padding: 12px 0;
  }

  .week {
    padding: 0 6px;
    flex-wrap: wrap;
  }

  .day-head {
    padding: 10px 12px 8px;
  }

  .day-total {
    padding-right: 78px;
  }

  .more {
    padding: 0 6px;
  }
}
</style>
