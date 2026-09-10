<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import ConfirmDialog from '@/components/ConfirmDialog.vue'
import EntryDialog from '@/components/EntryDialog.vue'
import EntryRow from '@/components/EntryRow.vue'
import TimerBar from '@/components/TimerBar.vue'
import { useAsyncAction } from '@/composables/useApiError'
import { useEntriesStore } from '@/stores/entries'
import { useProjectsStore } from '@/stores/projects'
import { useTimerStore } from '@/stores/timer'
import type { TimeEntry } from '@/types'
import { localDayKey, startOfLocalDay } from '@/utils/datetime'
import { formatCompact } from '@/utils/duration'

const { t, d } = useI18n()
const timer = useTimerStore()
const entries = useEntriesStore()
const projects = useProjectsStore()
const { busy: deleting, error: deleteError, run } = useAsyncAction()

const editing = ref<TimeEntry | null>(null)
const dialogOpen = ref(false)
const pendingDelete = ref<TimeEntry | null>(null)

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

function openEditor(entry: TimeEntry | null) {
  editing.value = entry
  dialogOpen.value = true
}

async function confirmDelete() {
  const entry = pendingDelete.value
  if (!entry) return
  await run(async () => {
    await entries.remove(entry.id)
    if (timer.entry?.id === entry.id) await timer.sync()
    pendingDelete.value = null
  })
}

/** Another device may have started or stopped the timer while this tab idled. */
async function resync() {
  if (document.visibilityState !== 'visible') return
  await Promise.all([timer.sync(), entries.load()])
}

onMounted(async () => {
  await projects.load()
  await Promise.all([timer.sync(), entries.load()])
  document.addEventListener('visibilitychange', resync)
  window.addEventListener('focus', resync)
})

onUnmounted(() => {
  document.removeEventListener('visibilitychange', resync)
  window.removeEventListener('focus', resync)
})
</script>

<template>
  <div class="page stack">
    <TimerBar @changed="entries.load()" />

    <section class="stack" style="gap: 8px">
      <div class="row-between">
        <h1>{{ t('entries.title') }}</h1>
        <button type="button" @click="openEditor(null)">{{ t('entries.addManual') }}</button>
      </div>

      <p v-if="deleteError" class="banner">{{ deleteError }}</p>

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
            @edit="openEditor"
            @remove="pendingDelete = $event"
          />
        </ul>
      </div>

      <div v-if="entries.items.length" class="row-between footer small muted">
        <span>{{ t('entries.showing', { shown: entries.items.length, total: entries.total }) }}</span>
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

    <EntryDialog
      :open="dialogOpen"
      :entry="editing"
      @close="dialogOpen = false"
      @saved="entries.load()"
    />

    <ConfirmDialog
      :open="pendingDelete !== null"
      :title="t('common.delete')"
      :message="t('entries.deleteConfirm')"
      :busy="deleting"
      @close="pendingDelete = null"
      @confirm="confirmDelete"
    />
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

.footer {
  padding: 0 4px;
}
</style>
