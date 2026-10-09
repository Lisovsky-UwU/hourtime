<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import * as reportsApi from '@/api/reports'
import UiButton from '@/components/ui/UiButton.vue'
import UiSegmented from '@/components/ui/UiSegmented.vue'
import { useDuration } from '@/composables/useDuration'
import { useReportData } from '@/composables/useReportData'
import { useReportQuery } from '@/composables/useReportQuery'
import { formatAmount } from '@/utils/money'
import { parseDateKey, toDateKey } from '@/utils/period'

/**
 * A week as a table: one row per project (or client), one column per day,
 * the way a paper timesheet is ruled. Empty cells stay empty rather than
 * printing zeros, so the days that were worked stand out.
 */
const { t, d, locale } = useI18n()
const duration = useDuration()
const report = useReportQuery()

type Grouping = 'project' | 'client'

const groupBy = computed<Grouping>({
  get: () => (report.state.value.groupBy === 'client' ? 'client' : 'project'),
  set: (value) => report.patch({ group: value }),
})

const groupOptions = computed(() =>
  (['project', 'client'] as const).map((value) => ({ value, label: t(`reports.group.${value}`) })),
)

const { data, loading, error, load } = useReportData(
  () => [report.filters.value, groupBy.value],
  () => reportsApi.weekly(report.filters.value, groupBy.value),
)

const priced = computed(() => data.value !== null && data.value.totals.amount !== '0.00')
const today = toDateKey(new Date())

function money(amount: string): string {
  return data.value ? formatAmount(amount, data.value.currency, locale.value) : ''
}

function cell(seconds: number): string {
  return seconds > 0 ? duration(seconds) : ''
}
</script>

<template>
  <div v-if="error && !data" class="alert" role="alert">
    <span>{{ t('reports.loadFailed') }} {{ error }}</span>
    <UiButton size="sm" @click="load">{{ t('common.retry') }}</UiButton>
  </div>

  <div
    v-else-if="!data"
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

  <section
    v-else
    class="sheet weekly"
    :data-loading="loading ? '' : undefined"
    :aria-busy="loading"
  >
    <header class="weekly-head">
      <UiSegmented v-model="groupBy" :options="groupOptions" :label="t('reports.group.label')" />
      <span v-if="error" class="error">{{ t('reports.loadFailed') }} {{ error }}</span>
    </header>

    <p v-if="!data.rows.length" class="empty muted">{{ t('reports.empty') }}</p>

    <div v-else class="table-wrap">
      <table class="data-table weekly-table">
        <thead>
          <tr>
            <th scope="col">{{ t(`reports.group.${groupBy}`) }}</th>
            <th
              v-for="day in data.days"
              :key="day"
              scope="col"
              class="num-col day"
              :data-today="day === today ? '' : undefined"
            >
              {{ d(parseDateKey(day), 'axisWeekday') }}
            </th>
            <th scope="col" class="num-col">{{ t('reports.totals.total') }}</th>
            <th v-if="priced" scope="col" class="num-col">{{ t('reports.totals.amount') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in data.rows" :key="row.id ?? ''">
            <th scope="row" class="row-head">
              <span class="name">
                <span
                  v-if="groupBy === 'project'"
                  class="row-dot"
                  :style="{ background: row.color ?? 'transparent' }"
                  :data-none="row.color ? undefined : ''"
                />
                <span :class="{ muted: row.name === null }">{{
                  row.name ?? t(`reports.without.${groupBy}`)
                }}</span>
                <span v-if="row.client_name" class="muted client">{{ row.client_name }}</span>
              </span>
            </th>
            <td v-for="(seconds, index) in row.days" :key="index" class="num-col num day">
              {{ cell(seconds) }}
            </td>
            <td class="num-col num total">{{ duration(row.duration) }}</td>
            <td v-if="priced" class="num-col num">
              {{ row.amount !== '0.00' ? money(row.amount) : '' }}
            </td>
          </tr>
        </tbody>
        <tfoot>
          <tr>
            <th scope="row" class="row-head">{{ t('reports.totals.total') }}</th>
            <td v-for="(seconds, index) in data.totals.days" :key="index" class="num-col num day">
              {{ cell(seconds) }}
            </td>
            <td class="num-col num total">{{ duration(data.totals.duration) }}</td>
            <td v-if="priced" class="num-col num total">{{ money(data.totals.amount) }}</td>
          </tr>
        </tfoot>
      </table>
    </div>
  </section>
</template>

<style scoped>
.weekly {
  overflow: hidden;
  transition: opacity var(--dur) var(--ease);
}

.weekly[data-loading] {
  opacity: 0.55;
}

.skeleton-sheet {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 24px;
}

.weekly-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 12px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
}

.error {
  color: var(--danger);
  font-size: var(--text-xs);
}

.empty {
  padding: 32px 16px;
  text-align: center;
}

.table-wrap {
  /* Relative: visually hidden labels are absolutely positioned, and without
     a containing block here they would stretch the page past the scroller. */
  position: relative;
  overflow-x: auto;
}

.weekly-table {
  min-width: 720px;
}

.weekly-table td,
.weekly-table tbody th {
  padding-block: 8px;
}

/* Row heads are <th> for screen readers but read as the row's name, not as
   the small pencil column heads of .data-table. */
.weekly-table .row-head {
  border-top: 1px solid var(--border);
  border-bottom: 0;
  color: var(--text);
  font-size: inherit;
  font-weight: 500;
  text-align: left;
}

.weekly-table tbody tr:first-child .row-head {
  border-top: none;
}

.name {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px 8px;
  overflow-wrap: anywhere;
}

.client {
  font-weight: 400;
}

.row-dot[data-none] {
  border: 1.5px solid var(--control-border);
}

/* Day columns share the width evenly, so the week reads as a ruled grid. */
.weekly-table .day {
  width: 8%;
  color: var(--text);
}

.weekly-table th.day {
  color: var(--text-muted);
}

/* Today's column head in ink: where you are in the week. */
.weekly-table th.day[data-today] {
  color: var(--text);
  font-weight: 600;
}

.weekly-table .total {
  color: var(--text);
  font-weight: 600;
}

/* The totals row is the bottom line of the card: a heavier rule above it. */
.weekly-table tfoot th,
.weekly-table tfoot td {
  padding: 10px 16px;
  border-top: 1.5px solid var(--border-strong);
  font-weight: 600;
}

.weekly-table tfoot th {
  text-align: left;
}
</style>
