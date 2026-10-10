<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import type { LocationQueryRaw } from 'vue-router'
import { PopoverAnchor, PopoverContent, PopoverPortal, PopoverRoot } from 'reka-ui'
import FullCalendar from '@fullcalendar/vue3'
import type {
  CalendarOptions,
  DateSelectArg,
  DatesSetArg,
  EventClickArg,
  EventDropArg,
  EventInput,
  FormatterInput,
} from '@fullcalendar/core'
import ruLocale from '@fullcalendar/core/locales/ru'
import interactionPlugin from '@fullcalendar/interaction'
import type { EventResizeDoneArg } from '@fullcalendar/interaction'
import timeGridPlugin from '@fullcalendar/timegrid'

import * as entriesApi from '@/api/timeEntries'
import type { EntryPatch } from '@/api/timeEntries'
import CalendarEntryBlock from '@/components/calendar/CalendarEntryBlock.vue'
import CalendarEntryEditor from '@/components/calendar/CalendarEntryEditor.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiIconButton from '@/components/ui/UiIconButton.vue'
import UiSegmented from '@/components/ui/UiSegmented.vue'
import { toast } from '@/components/ui/toast'
import { messageFor } from '@/composables/useApiError'
import { useDuration } from '@/composables/useDuration'
import { usePreferencesStore } from '@/stores/preferences'
import { useProjectsStore } from '@/stores/projects'
import { useTagsStore } from '@/stores/tags'
import { useTimerStore } from '@/stores/timer'
import { useWorkspaceStore } from '@/stores/workspace'
import type { TimeEntry } from '@/types'
import { localDayKey } from '@/utils/datetime'
import { addDays, formatPeriod, isDateKey, toDateKey } from '@/utils/period'
import { serverNow } from '@/utils/serverTime'

/**
 * Entries on a day or week time grid, as Toggl's calendar. The grid, drag,
 * resize, selection and touch are FullCalendar's; this view feeds it entries,
 * saves what it reports and dresses it in the app's tokens. View and date live
 * in the URL, like the reports.
 */
type Mode = 'week' | 'day'

const PAGE_SIZE = 200
const DAY_MS = 24 * 60 * 60 * 1000
const PLUGINS = [timeGridPlugin, interactionPlugin]
const LOCALES = [ruLocale]
const FC_VIEWS: Record<Mode, string> = { week: 'timeGridWeek', day: 'timeGridDay' }

const { t, d, locale } = useI18n()
const route = useRoute()
const router = useRouter()
const preferences = usePreferencesStore()
const projects = useProjectsStore()
const tags = useTagsStore()
const timer = useTimerStore()
const workspace = useWorkspaceStore()
const showDuration = useDuration()

// Read once: a phone opens on a day, a rotated tablet keeps what it had.
const narrow = window.matchMedia('(max-width: 767.98px)').matches

const mode = computed<Mode>(() => {
  const value = route.query.view
  return value === 'week' || value === 'day' ? value : narrow ? 'day' : 'week'
})
const anchorDate = computed(() => {
  const value = route.query.date
  return isDateKey(value) ? value : toDateKey(new Date())
})

function setQuery(values: Record<string, string | null>) {
  const query: LocationQueryRaw = { ...route.query }
  for (const [key, value] of Object.entries(values)) {
    if (value === null) delete query[key]
    else query[key] = value
  }
  void router.replace({ query })
}

const modeModel = computed({
  get: () => mode.value,
  set: (value: Mode) => setQuery({ view: value }),
})

function shift(direction: -1 | 1) {
  setQuery({ date: addDays(anchorDate.value, direction * (mode.value === 'week' ? 7 : 1)) })
}

function goToday() {
  setQuery({ date: null })
}

// ---------------------------------------------------------------- loading

/** What the grid shows, `end` exclusive; set by FullCalendar on every move. */
const range = ref<{ start: Date; end: Date } | null>(null)
const items = ref<TimeEntry[]>([])
/** Range of the entries on screen; differs from `range` while a new one loads. */
const loadedKey = ref('')
let loadSeq = 0

const rangeKey = computed(() =>
  range.value ? `${range.value.start.toISOString()}/${range.value.end.toISOString()}` : '',
)
const stale = computed(() => loadedKey.value !== rangeKey.value)

async function load() {
  const current = range.value
  if (!current) return
  const key = rangeKey.value
  const seq = ++loadSeq
  // A day early: an entry started the evening before still reaches into the range.
  // shortcut: an entry longer than a day that started even earlier is missed;
  // needs an "overlaps the range" filter in the API if such entries show up.
  const from = new Date(current.start.getTime() - DAY_MS)
  try {
    const found: TimeEntry[] = []
    for (let offset = 0; ; offset += PAGE_SIZE) {
      const page = await entriesApi.list({
        started_from: from.toISOString(),
        started_to: current.end.toISOString(),
        limit: PAGE_SIZE,
        offset,
      })
      found.push(...page.items)
      if (!page.has_more) break
    }
    // Only the latest request lands: a quick click through weeks fires several.
    if (seq !== loadSeq) return
    items.value = found
    loadedKey.value = key
  } catch (cause) {
    if (seq === loadSeq) toast.error(t('calendar.loadFailed'), messageFor(cause))
  }
}

watch(rangeKey, () => void load())

// Started, stopped or continued anywhere (the sidebar, another device): the
// grid gains or loses a running block, so it is read again.
watch(
  () => timer.entry?.id,
  () => void load(),
)

let pendingResync: number | null = null

function resync() {
  if (document.visibilityState !== 'visible' || pendingResync !== null) return
  pendingResync = window.setTimeout(() => {
    pendingResync = null
    void load()
  }, 100)
}

onMounted(() => {
  void workspace.load().catch(() => {})
  document.addEventListener('visibilitychange', resync)
  window.addEventListener('focus', resync)
})

// ---------------------------------------------------------------- entries

/** The timer store holds the freshest copy of the running entry. */
const shown = computed(() =>
  items.value.map((entry) => (entry.id === timer.entry?.id ? timer.entry : entry)),
)

/**
 * The running block's end, moved forward every half minute rather than every
 * second: each move re-lays the whole grid. Frozen while a block is dragged,
 * or the grid would drop the drag halfway.
 */
const now = ref(serverNow())
const interacting = ref(false)
const ticker = window.setInterval(() => {
  if (!interacting.value) now.value = serverNow()
}, 30_000)

onUnmounted(() => {
  window.clearInterval(ticker)
  if (pendingResync !== null) window.clearTimeout(pendingResync)
  document.removeEventListener('visibilitychange', resync)
  window.removeEventListener('focus', resync)
})

function endOf(entry: TimeEntry): number {
  const start = Date.parse(entry.started_at)
  return entry.stopped_at ? Date.parse(entry.stopped_at) : Math.max(now.value, start + 60_000)
}

/** Light tint of the project's color with a full-strength edge, text stays in ink. */
function colorsOf(entry: TimeEntry): { backgroundColor: string; borderColor: string } {
  if (entry.stopped_at === null) {
    return {
      backgroundColor: 'color-mix(in srgb, var(--live) 10%, var(--surface))',
      borderColor: 'var(--live)',
    }
  }
  const project = projects.find(entry.project_id)
  if (!project) return { backgroundColor: 'var(--surface-muted)', borderColor: 'var(--border-strong)' }
  return {
    backgroundColor: `color-mix(in srgb, ${project.color} 16%, var(--surface))`,
    borderColor: project.color,
  }
}

/**
 * An entry past midnight is one event; the grid itself cuts it into the part
 * up to 24:00 and the part from 00:00 the next day.
 */
const events = computed<EventInput[]>(() => {
  const current = range.value
  if (!current) return []
  const from = current.start.getTime()
  const to = current.end.getTime()
  return shown.value
    .filter((entry) => Date.parse(entry.started_at) < to && endOf(entry) > from)
    .map((entry) => ({
      id: entry.id,
      start: Date.parse(entry.started_at),
      end: endOf(entry),
      classNames: entry.stopped_at === null ? ['is-running'] : [],
      extendedProps: { entry },
      ...colorsOf(entry),
    }))
})

/** Day totals by the day an entry started, as on the timer page and in reports. */
const dayTotals = computed(() => {
  const totals = new Map<string, number>()
  for (const entry of shown.value) {
    const key = localDayKey(entry.started_at)
    totals.set(key, (totals.get(key) ?? 0) + timer.secondsOf(entry))
  }
  return totals
})

const title = computed(() => {
  const current = range.value
  if (!current) return ''
  if (mode.value === 'day') return d(current.start, 'weekdayYear')
  const last = new Date(current.end.getTime() - 1)
  return formatPeriod({ from: toDateKey(current.start), to: toDateKey(last) }, locale.value)
})

const showsToday = computed(() => {
  const current = range.value
  const time = Date.now()
  return !!current && current.start.getTime() <= time && time < current.end.getTime()
})

// ---------------------------------------------------------------- saving

function replace(saved: TimeEntry) {
  items.value = items.value.map((entry) => (entry.id === saved.id ? saved : entry))
}

/** Every write goes through here, so the timer bar hears about it too. */
async function save(id: string, patch: EntryPatch): Promise<TimeEntry> {
  const saved = await entriesApi.update(id, patch)
  replace(saved)
  timer.applySaved(saved)
  return saved
}

function entryOf(info: { event: { extendedProps: Record<string, unknown> } }): TimeEntry {
  return info.event.extendedProps.entry as TimeEntry
}

/**
 * A moved block keeps its length; a resized one gets a new end. A running
 * entry has no end yet: moving it shifts only its start, and it can be cut
 * short (which stops it) but not stretched past now.
 */
async function onChange(info: EventDropArg | EventResizeDoneArg, resized: boolean) {
  const entry = entryOf(info)
  const start = info.event.start
  const end = info.event.end
  if (!start || !end) return info.revert()

  let patch: EntryPatch
  if (entry.stopped_at === null) {
    const limit = serverNow()
    if ((resized ? end : start).getTime() >= limit) {
      info.revert()
      toast.error(t('calendar.runningLimit'))
      return
    }
    patch = resized ? { stopped_at: end.toISOString() } : { started_at: start.toISOString() }
  } else {
    patch = resized
      ? { stopped_at: end.toISOString() }
      : { started_at: start.toISOString(), stopped_at: end.toISOString() }
  }

  try {
    await save(entry.id, patch)
  } catch (cause) {
    info.revert()
    toast.error(messageFor(cause))
  }
}

async function onSelect(info: DateSelectArg) {
  try {
    const created = await entriesApi.create({
      started_at: info.start.toISOString(),
      stopped_at: info.end.toISOString(),
      description: '',
      project_id: null,
    })
    items.value = [...items.value, created]
    // The grid draws the block on the next render; the anchor looks it up then.
    await nextTick()
    openEditor(created.id, null)
  } catch (cause) {
    toast.error(messageFor(cause))
  } finally {
    info.view.calendar.unselect()
  }
}

// ---------------------------------------------------------------- editing

const editing = ref<{ id: string; el: HTMLElement | null } | null>(null)
let lastEditedId: string | null = null

const editingEntry = computed(() => {
  const id = editing.value?.id
  return id ? (shown.value.find((entry) => entry.id === id) ?? null) : null
})

function blockElement(id: string | null | undefined): HTMLElement | null {
  if (!id) return null
  return document.querySelector<HTMLElement>(`[data-entry-id="${id}"]`)?.closest('.fc-event') ?? null
}

/**
 * The popover hangs from the block, which the grid redraws after every save.
 * A virtual anchor looks the block up again instead of holding a stale node.
 */
const anchor = {
  getBoundingClientRect(): DOMRect {
    const current = editing.value
    const el = current?.el?.isConnected ? current.el : blockElement(current?.id)
    return el?.getBoundingClientRect() ?? new DOMRect()
  },
}

/** The id is bound now: the editor's last save runs after the popover has let go of it. */
function saveFor(id: string) {
  return (patch: EntryPatch) => save(id, patch)
}

function openEditor(id: string, el: HTMLElement | null) {
  editing.value = { id, el }
  lastEditedId = id
}

function onEventClick(info: EventClickArg) {
  openEditor(entryOf(info).id, info.el)
}

function onEditorOpen(open: boolean) {
  if (!open) editing.value = null
}

/** Back to the block, unless the click that closed the popover went elsewhere. */
function onEditorCloseFocus(event: Event) {
  event.preventDefault()
  const active = document.activeElement
  if (active && active !== document.body) return
  blockElement(lastEditedId)?.focus()
}

// ---------------------------------------------------------------- actions

const pendingDelete = ref<TimeEntry | null>(null)
const busy = ref(false)

function askRemove(entry: TimeEntry) {
  editing.value = null
  pendingDelete.value = entry
}

async function removeEntry() {
  const entry = pendingDelete.value
  if (!entry) return
  busy.value = true
  try {
    await entriesApi.remove(entry.id)
    items.value = items.value.filter((item) => item.id !== entry.id)
    if (timer.entry?.id === entry.id) timer.reset()
    pendingDelete.value = null
  } catch (cause) {
    // The dialog stays, so the user sees what they were doing.
    toast.error(messageFor(cause))
  } finally {
    busy.value = false
  }
}

/** As on the timer page: what cannot be assigned any more is left out. */
async function continueEntry(entry: TimeEntry) {
  editing.value = null
  try {
    await timer.start({
      description: entry.description,
      project_id: projects.find(entry.project_id)?.archived ? null : entry.project_id,
      tag_ids: entry.tag_ids.filter((id) => tags.byId.has(id)),
      billable: entry.billable,
    })
    // The new running entry arrives through the timer watch above.
  } catch (cause) {
    toast.error(messageFor(cause))
  }
}

// ---------------------------------------------------------------- grid

const calendar = ref<InstanceType<typeof FullCalendar> | null>(null)

watch([mode, anchorDate], ([nextMode, nextDate]) => {
  calendar.value?.getApi().changeView(FC_VIEWS[nextMode], nextDate)
})

/** Opens on the working day, or on the current hour when that is later or earlier. */
function initialScroll(): string {
  const hour = new Date().getHours()
  const target = hour >= 8 && hour < 16 ? 8 : Math.max(0, hour - 2)
  return `${String(target).padStart(2, '0')}:00:00`
}

const slotLabelFormat = computed<FormatterInput>(() =>
  preferences.hourCycle === '12'
    ? { hour: 'numeric', meridiem: 'short', hour12: true }
    : { hour: '2-digit', minute: '2-digit', hour12: false },
)

/** Fires again on every options reset; a new object for the same range would loop. */
function onDatesSet(info: DatesSetArg) {
  const current = range.value
  if (current?.start.getTime() === info.start.getTime() && current.end.getTime() === info.end.getTime()) return
  range.value = { start: info.start, end: info.end }
}

const startInteracting = () => (interacting.value = true)
const stopInteracting = () => {
  interacting.value = false
  now.value = serverNow()
}
const onDrop = (info: EventDropArg) => void onChange(info, false)
const onResize = (info: EventResizeDoneArg) => void onChange(info, true)

// FullCalendar reads these once; later moves go through `changeView` above.
const initialView = FC_VIEWS[mode.value]
const initialDate = anchorDate.value
const scrollTime = initialScroll()
// The grid's "now" is the server's, like the running timer's.
const gridNow = () => new Date(serverNow())

const options = computed<CalendarOptions>(() => ({
  plugins: PLUGINS,
  locales: LOCALES,
  locale: locale.value,
  initialView,
  initialDate,
  headerToolbar: false,
  height: '100%',
  firstDay: preferences.weekStart,
  allDaySlot: false,
  nowIndicator: true,
  now: gridNow,
  scrollTime,
  slotDuration: '00:30:00',
  snapDuration: '00:15:00',
  slotLabelFormat: slotLabelFormat.value,
  slotEventOverlap: false,
  eventMinHeight: 18,
  editable: true,
  eventResizableFromStart: false,
  selectable: true,
  selectMirror: true,
  // A plain click on empty time is not an entry; dragging across it is.
  selectMinDistance: 4,
  longPressDelay: 400,
  events: events.value,
  datesSet: onDatesSet,
  eventClick: onEventClick,
  eventDrop: onDrop,
  eventResize: onResize,
  eventDragStart: startInteracting,
  eventDragStop: stopInteracting,
  eventResizeStart: startInteracting,
  eventResizeStop: stopInteracting,
  select: onSelect,
}))
</script>

<template>
  <div class="calendar-page">
    <header class="calendar-head">
      <h1>{{ t('calendar.title') }}</h1>

      <div class="calendar-nav">
        <UiIconButton
          icon="chevron-left"
          :label="t(`calendar.previous.${mode}`)"
          @click="shift(-1)"
        />
        <UiIconButton icon="chevron-right" :label="t(`calendar.next.${mode}`)" @click="shift(1)" />
        <UiButton size="sm" :disabled="showsToday" @click="goToday">
          {{ t('entries.today') }}
        </UiButton>
      </div>

      <p class="calendar-title" aria-live="polite">{{ title }}</p>

      <UiSegmented
        v-model="modeModel"
        :label="t('calendar.views')"
        :options="[
          { value: 'week', label: t('calendar.view.week') },
          { value: 'day', label: t('calendar.view.day') },
        ]"
      />
    </header>

    <div class="sheet calendar-sheet" :data-stale="stale ? '' : undefined">
      <FullCalendar ref="calendar" class="cal-grid" :options="options">
        <template #dayHeaderContent="arg">
          <span class="cal-day" :data-today="arg.isToday ? '' : undefined">
            <span class="cal-day-name">{{ d(arg.date, 'axisWeekday') }}</span>
            <span v-if="dayTotals.get(toDateKey(arg.date))" class="cal-day-total num">
              {{ showDuration(dayTotals.get(toDateKey(arg.date)) ?? 0) }}
            </span>
          </span>
        </template>

        <template #eventContent="arg">
          <CalendarEntryBlock
            v-if="arg.event.extendedProps.entry"
            :entry="arg.event.extendedProps.entry"
            :start="arg.event.start"
            :end="arg.event.end ?? arg.event.start"
          />
          <span v-else class="cal-selection num">{{ arg.timeText }}</span>
        </template>
      </FullCalendar>
    </div>

    <PopoverRoot :open="editingEntry !== null" @update:open="onEditorOpen">
      <PopoverAnchor :reference="anchor" />
      <PopoverPortal>
        <PopoverContent
          class="ui-floating ui-popover"
          :side="narrow ? 'bottom' : 'right'"
          align="start"
          :side-offset="8"
          :collision-padding="8"
          update-position-strategy="always"
          :aria-label="t('calendar.editEntry')"
          @close-auto-focus="onEditorCloseFocus"
        >
          <CalendarEntryEditor
            v-if="editingEntry"
            :key="editingEntry.id"
            :entry="editingEntry"
            :save="saveFor(editingEntry.id)"
            @remove="askRemove"
            @continue="continueEntry"
          />
        </PopoverContent>
      </PopoverPortal>
    </PopoverRoot>

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
/* The grid scrolls inside its sheet; the page itself is one screen tall. */
.calendar-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: calc(100dvh - var(--topbar-h, 0px));
  min-height: 480px;
  max-width: var(--page-width-wide);
  margin: 0 auto;
  padding: 28px 24px 24px;
}

.calendar-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px 16px;
}

.calendar-head h1 {
  font-size: var(--text-xl);
}

.calendar-nav {
  display: inline-flex;
  align-items: center;
  gap: 2px;
}

.calendar-nav .ui-button {
  margin-left: 6px;
}

.calendar-title {
  flex: 1 1 auto;
  min-width: 0;
  font-size: var(--text-lg);
  font-weight: 500;
}

/* Russian weekdays come lowercase from Intl. */
.calendar-title::first-letter {
  text-transform: uppercase;
}

.calendar-sheet {
  flex: 1 1 auto;
  min-height: 0;
  transition: opacity var(--dur) var(--ease);
}

/* Another week is loading: the old one stays, muted, as in the reports. */
.calendar-sheet[data-stale] {
  opacity: 0.55;
}

@media (width < 768px) {
  .calendar-page {
    gap: 12px;
    padding: 12px 12px 12px;
  }

  .calendar-head h1 {
    display: none;
  }

  .calendar-title {
    order: 3;
    flex-basis: 100%;
    font-size: var(--text-md);
  }
}
</style>

<style>
/*
 * FullCalendar repainted with the app's tokens. Global, because the grid's
 * markup is FullCalendar's, not this component's; everything is kept under
 * .cal-grid. Its own stylesheet is injected first in <head>, so these rules
 * win at equal specificity.
 */
.cal-grid {
  --fc-border-color: var(--border);
  --fc-page-bg-color: var(--surface);
  --fc-neutral-bg-color: var(--surface-muted);
  --fc-neutral-text-color: var(--text-muted);
  --fc-today-bg-color: color-mix(in srgb, var(--accent) 4%, transparent);
  --fc-now-indicator-color: var(--text);
  --fc-highlight-color: var(--accent-soft);
  /* Only the selection being drawn uses these; entries carry their own colors. */
  --fc-event-bg-color: var(--accent-soft);
  --fc-event-border-color: var(--accent);
  --fc-event-text-color: var(--text);
  --fc-event-selected-overlay-color: transparent;
  --fc-small-font-size: var(--text-xs);

  height: 100%;
  color: var(--text);
  font-size: var(--text-sm);
}

/* The sheet draws the outer frame. */
.cal-grid .fc-scrollgrid {
  border: 0;
}

/* The header keeps an empty scrollbar so its columns line up with the body's;
   only its space is needed, not the arrows. */
.cal-grid .fc-scrollgrid-section-header .fc-scroller {
  scrollbar-color: transparent transparent;
}

.cal-grid .fc-col-header-cell {
  padding: 6px 4px;
  font-weight: 400;
  vertical-align: top;
}

.cal-day {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1px;
  color: var(--text-muted);
}

.cal-day[data-today] {
  color: var(--text);
  font-weight: 600;
}

.cal-day-name::first-letter {
  text-transform: uppercase;
}

.cal-day-total {
  color: var(--text);
  font-size: var(--text-xs);
  font-weight: 600;
}

/* 48 px an hour: a quarter-hour entry still holds one line of text. */
.cal-grid .fc-timegrid-slot {
  height: 24px;
}

/* Half-hours are a fainter rule than hours. */
.cal-grid .fc-timegrid-slot-minor {
  border-top-style: dotted;
}

.cal-grid .fc-timegrid-slot-label {
  vertical-align: top;
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-variant-numeric: tabular-nums;
  font-variation-settings: 'SHRP' 100;
}

.cal-grid .fc-timegrid-axis-cushion,
.cal-grid .fc-timegrid-slot-label-cushion {
  padding: 0 6px;
}

/* A block: tinted sheet with a full-color edge on the left. FullCalendar sets
   the colors inline; only the widths and shape are ours. */
.cal-grid .fc-v-event {
  border-width: 0 0 0 3px;
  border-radius: 4px;
  box-shadow: 0 0 0 1px var(--surface);
  cursor: pointer;
}

.cal-grid .fc-timegrid-event .fc-event-main {
  padding: 0;
}

/* Running: the bottom edge is still open, so it is drawn dashed. */
.cal-grid .fc-v-event.is-running {
  border-bottom: 2px dashed;
  border-bottom-color: var(--live);
}

.cal-grid .fc-event:focus {
  box-shadow: 0 0 0 1px var(--surface);
}

.cal-grid .fc-event:focus::after {
  display: none;
}

.cal-grid .fc-event:focus-visible {
  outline: 2px solid var(--focus);
  outline-offset: 1px;
  z-index: 5;
}

/* Lifted while carried, like any floating layer. */
.cal-grid .fc-event-dragging,
.cal-grid .fc-event-selected {
  box-shadow: var(--shadow-float);
}

.cal-grid .fc-timegrid-event .fc-event-resizer-end {
  cursor: ns-resize;
}

.cal-grid .fc-timegrid-now-indicator-line {
  border-top-width: 2px;
}

.cal-selection {
  display: block;
  padding: 2px 6px;
  color: var(--accent);
  font-size: var(--text-xs);
  font-weight: 600;
}
</style>
