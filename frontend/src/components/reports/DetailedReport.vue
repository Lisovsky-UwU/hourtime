<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import * as reportsApi from '@/api/reports'
import type { DetailedSort } from '@/api/reports'
import AppIcon from '@/components/AppIcon.vue'
import UiButton from '@/components/ui/UiButton.vue'
import { messageFor } from '@/composables/useApiError'
import { useDuration } from '@/composables/useDuration'
import { useReportQuery } from '@/composables/useReportQuery'
import { usePreferencesStore } from '@/stores/preferences'
import type { DetailedReport, DetailedReportItem } from '@/types'
import { currencySymbol, formatAmount } from '@/utils/money'
import { formatTimeOfDay, toTimeOfDay } from '@/utils/timeOfDay'

const PAGE = 50

const { t, d, locale } = useI18n()
const duration = useDuration()
const preferences = usePreferencesStore()
const report = useReportQuery()

const head = ref<DetailedReport | null>(null)
const items = ref<DetailedReportItem[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
let latest = 0

/** `more` appends the next page; anything else starts over from the first. */
async function load(more = false) {
  const id = ++latest
  loading.value = true
  error.value = null
  const { sort, order } = report.state.value
  try {
    const page = await reportsApi.detailed(
      report.filters.value,
      sort,
      order,
      PAGE,
      more ? items.value.length : 0,
    )
    if (id !== latest) return
    head.value = page
    items.value = more ? [...items.value, ...page.items] : page.items
  } catch (cause) {
    if (id === latest) error.value = messageFor(cause)
  } finally {
    if (id === latest) loading.value = false
  }
}

watch(
  () => [report.filters.value, report.state.value.sort, report.state.value.order],
  () => void load(),
  { immediate: true, deep: true },
)

const priced = computed(() => head.value !== null && head.value.totals.amount !== '0.00')

const symbol = computed(() => (head.value ? currencySymbol(head.value.currency, locale.value) : ''))

function money(amount: string | null): string {
  return amount !== null && head.value
    ? formatAmount(amount, head.value.currency, locale.value)
    : ''
}

/** A new column sorts its natural way first: longest and newest at the top, names A to Z. */
function sortBy(column: DetailedSort) {
  const { sort, order } = report.state.value
  if (sort === column) {
    report.patch({ order: order === 'desc' ? 'asc' : 'desc' })
    return
  }
  const natural = column === 'description' || column === 'project' ? 'asc' : 'desc'
  report.patch({ sort: column, order: natural })
}

function ariaSort(column: DetailedSort): 'ascending' | 'descending' | 'none' {
  const { sort, order } = report.state.value
  if (sort !== column) return 'none'
  return order === 'asc' ? 'ascending' : 'descending'
}

function interval(item: DetailedReportItem): string {
  const cycle = preferences.hourCycle
  return `${formatTimeOfDay(toTimeOfDay(item.started_at), cycle)} - ${formatTimeOfDay(toTimeOfDay(item.stopped_at, item.started_at), cycle)}`
}

const columns = computed(() => [
  { key: 'started_at' as const, label: t('reports.columns.date') },
  { key: 'description' as const, label: t('reports.columns.description') },
  { key: 'project' as const, label: t('reports.columns.project') },
])
</script>

<template>
  <div v-if="error && !head" class="alert" role="alert">
    <span>{{ t('reports.loadFailed') }} {{ error }}</span>
    <UiButton size="sm" @click="load()">{{ t('common.retry') }}</UiButton>
  </div>

  <div
    v-else-if="!head"
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

  <div
    v-else
    class="detailed"
    :data-loading="loading && !items.length ? '' : undefined"
    :aria-busy="loading"
  >
    <p class="summary-line">
      <span>{{ t('reports.totals.entriesCount', head.totals.entries) }}</span>
      <span
        >{{ t('reports.totals.total') }}
        <strong class="num">{{ duration(head.totals.duration) }}</strong></span
      >
      <span
        >{{ t('reports.totals.billable') }}
        <strong class="num">{{ duration(head.totals.billable_duration) }}</strong></span
      >
      <span v-if="priced"
        >{{ t('reports.totals.amount') }}
        <strong class="num">{{ money(head.totals.amount) }}</strong></span
      >
    </p>

    <div v-if="error" class="alert" role="alert">
      <span>{{ t('reports.loadFailed') }} {{ error }}</span>
      <UiButton size="sm" @click="load()">{{ t('common.retry') }}</UiButton>
    </div>

    <p v-if="!items.length" class="sheet empty muted">{{ t('reports.empty') }}</p>

    <div v-else class="sheet table-wrap">
      <table class="data-table detailed-table">
        <thead>
          <tr>
            <th
              v-for="column in columns"
              :key="column.key"
              scope="col"
              :aria-sort="ariaSort(column.key)"
            >
              <button type="button" class="sort" @click="sortBy(column.key)">
                {{ column.label }}
                <AppIcon
                  v-if="report.state.value.sort === column.key"
                  :name="report.state.value.order === 'asc' ? 'arrow-up' : 'arrow-down'"
                  :size="14"
                />
              </button>
            </th>
            <th scope="col">{{ t('reports.columns.tags') }}</th>
            <th scope="col" class="num-col">{{ t('reports.columns.time') }}</th>
            <th scope="col" class="num-col" :aria-sort="ariaSort('duration')">
              <button type="button" class="sort" @click="sortBy('duration')">
                {{ t('reports.duration') }}
                <AppIcon
                  v-if="report.state.value.sort === 'duration'"
                  :name="report.state.value.order === 'asc' ? 'arrow-up' : 'arrow-down'"
                  :size="14"
                />
              </button>
            </th>
            <th v-if="priced" scope="col" class="num-col">{{ t('reports.totals.amount') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.id">
            <td class="date num">{{ d(new Date(item.started_at), 'dayShort') }}</td>
            <td class="description">
              <span v-if="item.description">{{ item.description }}</span>
              <span v-else class="muted">{{ t('reports.without.description') }}</span>
            </td>
            <td class="project">
              <span v-if="item.project" class="project-name">
                <span class="row-dot" :style="{ background: item.project.color }" />
                <span>
                  {{ item.project.name }}
                  <span v-if="item.client" class="muted">&nbsp;{{ item.client.name }}</span>
                </span>
              </span>
            </td>
            <td class="tags muted">{{ item.tags.map((tag) => tag.name).join(', ') }}</td>
            <td class="num-col num">{{ interval(item) }}</td>
            <td class="num-col num duration">
              <span v-if="item.billable" class="billable-mark" :title="t('billing.billable')">
                <span aria-hidden="true">{{ symbol }}</span>
                <span class="visually-hidden">{{ t('billing.billable') }}</span>
              </span>
              {{ duration(item.duration) }}
            </td>
            <td v-if="priced" class="num-col num">{{ money(item.amount) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <footer v-if="head.has_more" class="more">
      <UiButton :disabled="loading" @click="load(true)">
        {{
          loading
            ? t('common.loading')
            : t('reports.loadMore', { shown: items.length, total: head.totals.entries })
        }}
      </UiButton>
    </footer>
  </div>
</template>

<style scoped>
.detailed {
  display: flex;
  flex-direction: column;
  gap: 12px;
  transition: opacity var(--dur) var(--ease);
}

.detailed[data-loading] {
  opacity: 0.55;
}

.skeleton-sheet {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 24px;
}

.summary-line {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 24px;
  padding: 0 4px;
  color: var(--text-muted);
}

.summary-line strong {
  color: var(--text);
  font-weight: 600;
}

.empty {
  padding: 32px 16px;
  text-align: center;
}

/* Wide tables scroll inside their sheet on phones, never the page. */
.table-wrap {
  /* Relative: visually hidden labels are absolutely positioned, and without
     a containing block here they would stretch the page past the scroller. */
  position: relative;
  overflow-x: auto;
}

.detailed-table {
  min-width: 760px;
}

.detailed-table td {
  padding-block: 8px;
  vertical-align: top;
}

.sort {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 0;
  border: 0;
  background: none;
  color: inherit;
  font: inherit;
  cursor: pointer;
}

.sort:hover {
  color: var(--text);
}

.date {
  color: var(--text-muted);
  white-space: nowrap;
}

.description {
  min-width: 200px;
  overflow-wrap: anywhere;
}

/* The dot stays on the first line of a long name that wraps. */
.project-name {
  display: inline-flex;
  align-items: baseline;
  gap: 8px;
  overflow-wrap: anywhere;
}

.project-name .row-dot {
  transform: translateY(-1px);
}

.tags {
  font-size: var(--text-xs);
}

.duration {
  color: var(--text);
  font-weight: 500;
}

/* The billable mark of the entry rows: the currency symbol in sharp ink. */
.billable-mark {
  margin-right: 6px;
  font-weight: 600;
  font-variation-settings: 'SHRP' 100;
}

.more {
  display: flex;
  justify-content: center;
}

@media print {
  .more {
    display: none;
  }
}
</style>
