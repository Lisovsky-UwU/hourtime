<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import * as entriesApi from '@/api/timeEntries'
import AppIcon from '@/components/AppIcon.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import ProjectPicker from '@/components/ProjectPicker.vue'
import TimesheetCell from '@/components/timesheet/TimesheetCell.vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiIconButton from '@/components/ui/UiIconButton.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiPopover from '@/components/ui/UiPopover.vue'
import UiSegmented from '@/components/ui/UiSegmented.vue'
import UiWeekCalendar from '@/components/ui/UiWeekCalendar.vue'
import { toast } from '@/components/ui/toast'
import { messageFor } from '@/composables/useApiError'
import { useDuration } from '@/composables/useDuration'
import { useClientsStore } from '@/stores/clients'
import { usePreferencesStore } from '@/stores/preferences'
import { useProjectsStore } from '@/stores/projects'
import { useTimerStore } from '@/stores/timer'
import type { TimeEntry } from '@/types'
import { localDayKey } from '@/utils/datetime'
import { addDays, formatPeriod, isDateKey, parseDateKey, toDateKey, weekOf } from '@/utils/period'
import { serverNow } from '@/utils/serverTime'
import type { CellChange, CellEntry } from '@/utils/timesheet'
import { planCellChange } from '@/utils/timesheet'

/**
 * A week as a paper timesheet: one row per project (or client, or project and
 * description), one column per day, and the day's total typed straight into
 * the cell. Days are the browser's, like the timer and the calendar; an entry
 * counts on the day it started. Rows by client are only for reading: a new
 * entry there would have no project to go to.
 */
const PAGE_SIZE = 200

const { t, d, locale } = useI18n()
const route = useRoute()
const router = useRouter()
const preferences = usePreferencesStore()
const projects = useProjectsStore()
const clients = useClientsStore()
const timer = useTimerStore()
const duration = useDuration()

const anchorDate = computed(() => {
  const value = route.query.date
  return isDateKey(value) ? value : toDateKey(new Date())
})
const week = computed(() => weekOf(anchorDate.value, preferences.weekStart))
const days = computed(() =>
  Array.from({ length: 7 }, (_, index) => addDays(week.value.from, index)),
)
const today = ref(toDateKey(new Date()))
const showsToday = computed(() => days.value.includes(today.value))

type Grouping = 'project' | 'client' | 'description'

/** Defaults are left out of the URL, as in the reports and the calendar. */
function setQuery(key: string, value: string | null) {
  const query = { ...route.query }
  if (value === null) delete query[key]
  else query[key] = value
  void router.replace({ query })
}

const grouping = computed<Grouping>({
  get: () => {
    const value = route.query.group
    return value === 'client' || value === 'description' ? value : 'project'
  },
  set: (value) => setQuery('group', value === 'project' ? null : value),
})

const groupOptions = computed(() =>
  (['project', 'client', 'description'] as const).map((value) => ({
    value,
    label: t(`reports.group.${value}`),
  })),
)

function shift(direction: -1 | 1) {
  setQuery('date', addDays(anchorDate.value, direction * 7))
}

function goToday() {
  setQuery('date', null)
}

const weekPickerOpen = ref(false)

function pickWeek(day: string) {
  weekPickerOpen.value = false
  setQuery('date', day)
}

// ---------------------------------------------------------------- loading

const items = ref<TimeEntry[]>([])
const loaded = ref(false)
const loadedWeek = ref('')
let loadSeq = 0

async function load() {
  const { from, to } = week.value
  const seq = ++loadSeq
  try {
    const found: TimeEntry[] = []
    for (let offset = 0; ; offset += PAGE_SIZE) {
      const page = await entriesApi.list({
        started_from: parseDateKey(from).toISOString(),
        // Inclusive on the server: the last millisecond of the week's last day.
        started_to: new Date(parseDateKey(addDays(to, 1)).getTime() - 1).toISOString(),
        limit: PAGE_SIZE,
        offset,
      })
      found.push(...page.items)
      if (!page.has_more) break
    }
    if (seq !== loadSeq) return
    items.value = found
    loaded.value = true
    loadedWeek.value = from
  } catch (cause) {
    if (seq === loadSeq) toast.error(t('timesheet.loadFailed'), messageFor(cause))
  }
}

// Started or stopped anywhere: a cell gains or loses its running entry.
watch(
  () => timer.entry?.id,
  () => void load(),
)

function resync() {
  if (document.visibilityState !== 'visible') return
  today.value = toDateKey(new Date())
  void load()
}

onMounted(() => {
  document.addEventListener('visibilitychange', resync)
  window.addEventListener('focus', resync)
})

onUnmounted(() => {
  document.removeEventListener('visibilitychange', resync)
  window.removeEventListener('focus', resync)
})

// ---------------------------------------------------------------- rows

interface Row {
  key: string
  /** Null both for "without project" and in rows by client. */
  projectId: string | null
  clientId: string | null
  /** Only in rows by description; new entries of other rows get none. */
  description: string
}

function rowOf(projectId: string | null, description: string): Row {
  if (grouping.value === 'client') {
    const clientId = projects.find(projectId)?.client_id ?? null
    return { key: `c:${clientId ?? ''}`, projectId: null, clientId, description: '' }
  }
  const text = grouping.value === 'description' ? description : ''
  return { key: `p:${projectId ?? ''}\n${text}`, projectId, clientId: null, description: text }
}

const editable = computed(() => grouping.value !== 'client')

/** The timer store holds the freshest copy of the running entry. */
const shown = computed(() =>
  items.value.map((entry) => (entry.id === timer.entry?.id ? timer.entry : entry)),
)

/** Entries by row, then by day. */
const cells = computed(() => {
  const byRow = new Map<string, Map<string, TimeEntry[]>>()
  for (const entry of shown.value) {
    const { key } = rowOf(entry.project_id, entry.description)
    const row = byRow.get(key) ?? new Map<string, TimeEntry[]>()
    const day = localDayKey(entry.started_at)
    row.set(day, [...(row.get(day) ?? []), entry])
    byRow.set(key, row)
  }
  return byRow
})

/** Rows added by hand this week; they stay last, so a row does not jump while typed into. */
const addedRows = ref<Row[]>([])

const rows = computed<Row[]>(() => {
  const added = new Set(addedRows.value.map((row) => row.key))
  const fromEntries = new Map<string, Row>()
  for (const entry of shown.value) {
    const row = rowOf(entry.project_id, entry.description)
    if (!added.has(row.key)) fromEntries.set(row.key, row)
  }
  // Rows without a project or client have no name and come first.
  const name = (row: Row) =>
    (grouping.value === 'client' ? clients.find(row.clientId) : projects.find(row.projectId))
      ?.name ?? ''
  const sorted = [...fromEntries.values()].sort(
    (a, b) =>
      name(a).localeCompare(name(b), locale.value) ||
      a.description.localeCompare(b.description, locale.value),
  )
  return [...sorted, ...addedRows.value]
})

watch(
  () => week.value.from,
  () => {
    addedRows.value = []
    void load()
  },
  { immediate: true },
)

function entriesOf(row: Row, day: string): TimeEntry[] {
  return cells.value.get(row.key)?.get(day) ?? []
}

function secondsOf(list: TimeEntry[]): number {
  return list.reduce((sum, entry) => sum + timer.secondsOf(entry), 0)
}

const rowTotal = (row: Row) =>
  days.value.reduce((sum, day) => sum + secondsOf(entriesOf(row, day)), 0)

const dayTotals = computed(() =>
  days.value.map((day) =>
    secondsOf(shown.value.filter((entry) => localDayKey(entry.started_at) === day)),
  ),
)
const weekTotal = computed(() => dayTotals.value.reduce((sum, seconds) => sum + seconds, 0))

function rowName(row: Row): string {
  if (grouping.value === 'client') {
    return clients.find(row.clientId)?.name ?? t('reports.without.client')
  }
  return projects.find(row.projectId)?.name ?? t('timer.noProject')
}

function cellLabel(row: Row, day: string): string {
  return t('timesheet.cellLabel', {
    row: [rowName(row), row.description].filter(Boolean).join(', '),
    day: d(parseDateKey(day), 'weekdayYear'),
  })
}

// ---------------------------------------------------------------- editing

const confirming = ref<{ count: number; resolve: (ok: boolean) => void } | null>(null)

function askToDelete(count: number): Promise<boolean> {
  return new Promise((resolve) => (confirming.value = { count, resolve }))
}

function answer(ok: boolean) {
  confirming.value?.resolve(ok)
  confirming.value = null
}

async function apply(row: Row, change: CellChange) {
  if (change.kind === 'create') {
    const created = await entriesApi.create({
      started_at: new Date(change.startedAt).toISOString(),
      stopped_at: new Date(change.stoppedAt).toISOString(),
      project_id: row.projectId,
      description: row.description,
    })
    items.value = [...items.value, created]
  } else if (change.kind === 'shorten') {
    const saved = await entriesApi.update(change.id, {
      stopped_at: new Date(change.stoppedAt).toISOString(),
    })
    items.value = items.value.map((entry) => (entry.id === saved.id ? saved : entry))
  } else {
    await entriesApi.remove(change.id)
    items.value = items.value.filter((entry) => entry.id !== change.id)
  }
}

function commitFor(row: Row, day: string) {
  return async (seconds: number): Promise<boolean> => {
    const dayStart = parseDateKey(day).getTime()
    const ends = shown.value
      .filter((entry) => localDayKey(entry.started_at) === day)
      .map((entry) => (entry.stopped_at ? Date.parse(entry.stopped_at) : serverNow()))
    const plan = planCellChange(
      // A cell with a running entry is read-only, so every entry here is stopped.
      entriesOf(row, day) as CellEntry[],
      seconds,
      {
        dayStart,
        dayEnd: parseDateKey(addDays(day, 1)).getTime(),
        lastEnd: ends.length ? Math.max(...ends) : null,
        now: serverNow(),
      },
    )
    if (plan === null) {
      toast.error(t('timesheet.noRoom'))
      return false
    }
    const deletes = plan.filter((change) => change.kind === 'delete').length
    if (deletes > 0 && !(await askToDelete(deletes))) return false

    try {
      for (const change of plan) await apply(row, change)
      return true
    } catch (cause) {
      toast.error(t('timesheet.saveFailed'), messageFor(cause))
      // Some changes may have landed before the failure; show what the server has.
      await load()
      return false
    }
  }
}

function isRunning(row: Row, day: string): boolean {
  return entriesOf(row, day).some((entry) => entry.stopped_at === null)
}

// ---------------------------------------------------------------- adding a row

const adding = ref(false)
const newProject = ref<string | null>(null)
const newDescription = ref('')

function startAdding() {
  newProject.value = null
  newDescription.value = ''
  adding.value = true
}

async function addRow() {
  const row = rowOf(newProject.value, newDescription.value.trim())
  if (!rows.value.some((existing) => existing.key === row.key))
    addedRows.value = [...addedRows.value, row]
  adding.value = false
  // Straight into the row's first day that takes time, today if it is on screen.
  await nextTick()
  const day = showsToday.value ? today.value : days.value.find((key) => key <= today.value)
  document
    .querySelector<HTMLInputElement>(
      `[data-row="${CSS.escape(row.key)}"] [data-day="${day}"] input`,
    )
    ?.focus()
}

const title = computed(() => formatPeriod(week.value, locale.value))

watch(grouping, () => {
  addedRows.value = []
  adding.value = false
})
</script>

<template>
  <div class="timesheet-page">
    <header class="timesheet-head">
      <h1>{{ t('timesheet.title') }}</h1>

      <div class="timesheet-nav">
        <UiIconButton icon="chevron-left" :label="t('calendar.previous.week')" @click="shift(-1)" />
        <UiIconButton icon="chevron-right" :label="t('calendar.next.week')" @click="shift(1)" />
        <UiButton size="sm" :disabled="showsToday" @click="goToday">
          {{ t('timesheet.thisWeek') }}
        </UiButton>
      </div>

      <UiPopover v-model:open="weekPickerOpen">
        <template #trigger>
          <button
            type="button"
            class="week-trigger"
            :aria-label="`${t('timesheet.pickWeek')}: ${title}`"
          >
            <AppIcon name="calendar" :size="16" />
            <span aria-live="polite">{{ title }}</span>
          </button>
        </template>
        <UiWeekCalendar :date="anchorDate" @select="pickWeek" />
      </UiPopover>

      <UiSegmented v-model="grouping" :options="groupOptions" :label="t('reports.group.label')" />
    </header>

    <div
      v-if="!loaded"
      class="sheet skeleton-sheet"
      role="status"
      :aria-label="t('common.loading')"
    >
      <span
        v-for="n in 4"
        :key="n"
        class="skeleton"
        aria-hidden="true"
        :style="{ width: `${30 + n * 12}%` }"
      />
    </div>

    <section v-else class="sheet timesheet" :data-stale="loadedWeek !== week.from ? '' : undefined">
      <div class="table-wrap">
        <table class="timesheet-table">
          <thead>
            <tr>
              <th scope="col" class="row-head">{{ t(`reports.group.${grouping}`) }}</th>
              <th
                v-for="day in days"
                :key="day"
                scope="col"
                class="day"
                :data-today="day === today ? '' : undefined"
              >
                {{ d(parseDateKey(day), 'axisWeekday') }}
              </th>
              <th scope="col" class="total">{{ t('reports.totals.total') }}</th>
            </tr>
          </thead>

          <tbody>
            <tr v-if="!rows.length && !adding">
              <td :colspan="days.length + 2" class="empty muted">{{
                editable ? t('timesheet.empty') : t('timesheet.emptyReadonly')
              }}</td>
            </tr>

            <tr v-for="row in rows" :key="row.key" :data-row="row.key">
              <th scope="row" class="row-head">
                <span class="row-label">
                  <span class="row-project">
                    <span
                      v-if="grouping !== 'client'"
                      class="row-dot"
                      :style="{ background: projects.find(row.projectId)?.color ?? 'transparent' }"
                      :data-none="row.projectId ? undefined : ''"
                    />
                    <span :class="{ muted: !(row.projectId ?? row.clientId) }">{{
                      rowName(row)
                    }}</span>
                  </span>
                  <span
                    v-if="grouping === 'description'"
                    class="row-description"
                    :class="{ muted: !row.description }"
                  >
                    {{ row.description || t('timer.noDescription') }}
                  </span>
                </span>
              </th>
              <td
                v-for="day in days"
                :key="day"
                class="day"
                :data-day="day"
                :data-today="day === today ? '' : undefined"
              >
                <TimesheetCell
                  :seconds="secondsOf(entriesOf(row, day))"
                  :label="cellLabel(row, day)"
                  :readonly="!editable || day > today || isRunning(row, day)"
                  :running="isRunning(row, day)"
                  :commit="commitFor(row, day)"
                />
              </td>
              <td class="total num">{{ rowTotal(row) ? duration(rowTotal(row)) : '' }}</td>
            </tr>

            <tr v-if="editable" class="add-row">
              <td :colspan="days.length + 2">
                <form v-if="adding" class="add-form" @submit.prevent="addRow">
                  <ProjectPicker v-model="newProject" />
                  <UiInput
                    v-if="grouping === 'description'"
                    v-model="newDescription"
                    class="add-description"
                    :placeholder="t('entries.edit.descriptionPlaceholder')"
                    :aria-label="t('entries.edit.description')"
                  />
                  <UiButton type="submit" variant="primary" size="sm">{{
                    t('timesheet.addRow')
                  }}</UiButton>
                  <UiButton size="sm" variant="ghost" @click="adding = false">{{
                    t('common.cancel')
                  }}</UiButton>
                </form>
                <UiButton v-else size="sm" variant="ghost" icon="plus" @click="startAdding">
                  {{ t('timesheet.addRow') }}
                </UiButton>
              </td>
            </tr>
          </tbody>

          <tfoot>
            <tr>
              <th scope="row" class="row-head">{{ t('reports.totals.total') }}</th>
              <td
                v-for="(seconds, index) in dayTotals"
                :key="index"
                class="day num"
                :data-today="days[index] === today ? '' : undefined"
              >
                {{ seconds ? duration(seconds) : '' }}
              </td>
              <td class="total num">{{ duration(weekTotal) }}</td>
            </tr>
          </tfoot>
        </table>
      </div>
    </section>

    <p class="hint muted">{{ editable ? t('timesheet.hint') : t('timesheet.clientHint') }}</p>

    <ConfirmDialog
      :open="confirming !== null"
      :title="t('timesheet.deleteTitle')"
      :message="t('timesheet.deleteConfirm', confirming?.count ?? 0)"
      :confirm-label="t('timesheet.deleteAction')"
      @close="answer(false)"
      @confirm="answer(true)"
    />
  </div>
</template>

<style scoped>
.timesheet-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: var(--page-width-wide);
  margin: 0 auto;
  padding: 28px 24px 24px;
}

.timesheet-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px 16px;
}

.timesheet-head h1 {
  font-size: var(--text-xl);
}

.timesheet-nav {
  display: inline-flex;
  align-items: center;
  gap: 2px;
}

.timesheet-nav .ui-button {
  margin-left: 6px;
}

/* The week's dates open the month to pick another week: the period picker's look. */
.week-trigger {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: var(--control-h);
  margin-right: auto;
  padding: 0 12px;
  border: 1px solid var(--control-border);
  border-radius: var(--radius);
  background: var(--surface);
  color: var(--text);
  font: inherit;
  font-weight: 500;
  cursor: pointer;
  transition: background-color var(--dur) var(--ease);
}

.week-trigger:hover,
.week-trigger[data-state='open'] {
  background: var(--surface-muted);
}

.week-trigger > svg {
  color: var(--text-muted);
}

.skeleton-sheet {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 24px;
}

.timesheet {
  overflow: hidden;
  transition: opacity var(--dur) var(--ease);
}

/* Another week is loading: the old one stays, muted, as in the reports. */
.timesheet[data-stale] {
  opacity: 0.55;
}

.table-wrap {
  overflow-x: auto;
}

.timesheet-table {
  width: 100%;
  min-width: 760px;
  border-collapse: separate;
  border-spacing: 0;
}

.timesheet-table th,
.timesheet-table td {
  padding: 4px;
  border-bottom: 1px solid var(--border);
  vertical-align: middle;
}

thead th {
  padding-block: 10px;
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-weight: 500;
  text-align: right;
}

/* Lined up with the figures in the cells below, which sit inside their own padding. */
.timesheet-table thead th.day {
  padding-inline: 12px;
}

/* Russian weekdays come lowercase from Intl. */
thead th.day::first-letter {
  text-transform: uppercase;
}

/* Today's column: ink in the head, a breath of the form's green down the column. */
th.day[data-today] {
  color: var(--text);
  font-weight: 600;
}

.day[data-today] {
  background: color-mix(in srgb, var(--accent) 4%, transparent);
}

/* Day columns share the width evenly, so the week reads as a ruled grid. */
.day {
  width: 9%;
}

.timesheet-table .total {
  width: 9%;
  padding-inline: 12px;
  color: var(--text);
  font-weight: 600;
  text-align: right;
}

.timesheet-table thead th.total {
  color: var(--text-muted);
  font-weight: 500;
}

/* The row's name stays put while the days scroll under it on a phone. */
.timesheet-table .row-head {
  position: sticky;
  left: 0;
  z-index: 1;
  min-width: 200px;
  padding-inline: 16px 12px;
  background: var(--surface);
  text-align: left;
}

.timesheet-table tbody .row-head {
  padding-block: 8px;
  font-weight: 400;
}

.row-label {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.row-project {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  overflow-wrap: anywhere;
}

.row-description {
  padding-left: 16px;
  font-size: var(--text-xs);
  overflow-wrap: anywhere;
}

.row-description:not(.muted) {
  color: var(--text-muted);
}

.row-dot[data-none] {
  border: 1.5px solid var(--control-border);
}

.empty {
  padding: 32px 16px;
  text-align: center;
}

.add-row td {
  padding: 8px 12px;
}

.add-form {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.add-description {
  flex: 1 1 240px;
  max-width: 420px;
}

/* The totals row is the bottom line of the card: a heavier rule above it. */
tfoot th,
tfoot td {
  padding-block: 10px;
  border-top: 1.5px solid var(--border-strong);
  border-bottom: 0;
  font-weight: 600;
}

tfoot td.day {
  padding-inline: 12px;
  text-align: right;
}

.hint {
  font-size: var(--text-xs);
}

@media (width < 768px) {
  .timesheet-page {
    gap: 12px;
    padding: 12px;
  }

  .timesheet-head h1 {
    display: none;
  }

  .timesheet-table .row-head {
    min-width: 140px;
  }
}
</style>
