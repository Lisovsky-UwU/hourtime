<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'

import AppIcon from '@/components/AppIcon.vue'
import EntryRow from '@/components/EntryRow.vue'
import TimerBar from '@/components/TimerBar.vue'
import { useAsyncAction } from '@/composables/useApiError'
import { useEntriesStore } from '@/stores/entries'
import { useProjectsStore } from '@/stores/projects'
import { useTimerStore } from '@/stores/timer'
import type { TimeEntry } from '@/types'
import { localDayKey, startOfLocalDay } from '@/utils/datetime'
import { formatCompact } from '@/utils/duration'
import { serverNow } from '@/utils/serverTime'

const HOUR_MS = 60 * 60 * 1000

const { t, d } = useI18n()
const timer = useTimerStore()
const entries = useEntriesStore()
const projects = useProjectsStore()
const { busy, error, run } = useAsyncAction()

const todayKey = localDayKey(startOfLocalDay().toISOString())
const yesterdayKey = localDayKey(startOfLocalDay(-1).toISOString())

interface DayGroup {
  key: string
  label: string
  totalSeconds: number
  items: TimeEntry[]
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
    items,
  }))
})

function labelFor(key: string, sample: TimeEntry | undefined): string {
  if (key === todayKey) return t('entries.today')
  if (key === yesterdayKey) return t('entries.yesterday')
  return sample ? d(new Date(sample.started_at), 'weekday') : key
}

/**
 * Adds a finished entry covering the last hour, ready to be adjusted in place.
 * There is no form to fill in first — the row itself is the form.
 */
async function addEntry() {
  const now = serverNow()
  await run(() =>
    entries.create({
      started_at: new Date(now - HOUR_MS).toISOString(),
      stopped_at: new Date(now).toISOString(),
      description: '',
      project_id: null,
    }),
  )
}

async function removeEntry(entry: TimeEntry) {
  await run(async () => {
    await entries.remove(entry.id)
    if (timer.entry?.id === entry.id) timer.reset()
  })
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

onMounted(async () => {
  await projects.load()
  await Promise.all([timer.sync(), entries.load()])
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
  <div class="page stack">
    <TimerBar />

    <section class="stack" style="gap: 8px">
      <div class="row-between">
        <h1>{{ t('entries.title') }}</h1>
        <button type="button" class="row add" :disabled="busy" @click="addEntry">
          <AppIcon name="plus" :size="16" />
          {{ t('entries.addManual') }}
        </button>
      </div>

      <p v-if="error" class="banner">{{ error }}</p>

      <p v-if="!entries.items.length && !entries.loading" class="card empty">
        {{ t('entries.empty') }}
      </p>

      <div v-for="group in groups" :key="group.key" class="card group">
        <header class="group-head">
          <h2>{{ group.label }}</h2>
          <span class="muted small mono">
            {{ t('entries.dayTotal', { duration: formatCompact(group.totalSeconds) }) }}
          </span>
        </header>

        <ul class="list">
          <EntryRow
            v-for="entry in group.items"
            :key="entry.id"
            :entry="entry"
            @remove="removeEntry"
          />
        </ul>
      </div>

      <div v-if="entries.items.length" class="row-between footer small muted">
        <span>{{ t('entries.showing', entries.items.length) }}</span>
        <button
          v-if="entries.hasMore"
          type="button"
          :disabled="entries.loading"
          @click="entries.loadMore()"
        >
          {{ entries.loading ? t('common.loading') : t('entries.loadMore') }}
        </button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.group {
  overflow: hidden;
}

.group-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 16px;
  background: var(--surface-muted);
  border-bottom: 1px solid var(--border);
}

.group-head h2 {
  font-size: 0.95rem;
}

.list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.add {
  gap: 6px;
}

.footer {
  padding: 0 4px;
}
</style>
