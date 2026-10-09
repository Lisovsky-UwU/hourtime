<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import * as reportsApi from '@/api/reports'
import type { SummaryGrouping } from '@/api/reports'
import AppIcon from '@/components/AppIcon.vue'
import DayChart from '@/components/reports/DayChart.vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiCombobox from '@/components/ui/UiCombobox.vue'
import UiSegmented from '@/components/ui/UiSegmented.vue'
import { useDuration } from '@/composables/useDuration'
import { useReportData } from '@/composables/useReportData'
import { useReportQuery } from '@/composables/useReportQuery'
import type { ReportGroup } from '@/types'
import { formatAmount } from '@/utils/money'

const { t, locale } = useI18n()
const duration = useDuration()
const report = useReportQuery()

const { data, loading, error, load } = useReportData(
  () => [report.filters.value, report.state.value.groupBy, report.state.value.subgroupBy],
  () =>
    reportsApi.summary(
      report.filters.value,
      report.state.value.groupBy,
      report.state.value.subgroupBy,
    ),
)

/** No money columns at all when nothing in the period has a price, not a column of zeros. */
const priced = computed(() => data.value !== null && data.value.totals.amount !== '0.00')

function money(amount: string): string {
  return priced.value && data.value ? formatAmount(amount, data.value.currency, locale.value) : ''
}

const groupOptions = computed(() =>
  (['project', 'client', 'tag', 'description'] as const).map((value) => ({
    value,
    label: t(`reports.group.${value}`),
  })),
)

const groupBy = computed({
  get: () => report.state.value.groupBy,
  set: (value: SummaryGrouping) => report.patch({ group: value }),
})

const subgroupItems = computed(() =>
  groupOptions.value.filter((option) => option.value !== report.state.value.groupBy),
)

const subgroupBy = computed({
  get: () => report.state.value.subgroupBy,
  set: (value: string | null) => report.patch({ sub: value ?? 'none' }),
})

function nameOf(group: ReportGroup, grouping: SummaryGrouping): string {
  return group.name ?? t(`reports.without.${grouping}`)
}

function share(group: ReportGroup): number {
  const total = data.value?.totals.duration ?? 0
  return total > 0 ? group.duration / total : 0
}

function percent(value: number): string {
  return new Intl.NumberFormat(locale.value, {
    style: 'percent',
    maximumFractionDigits: value < 0.1 ? 1 : 0,
  }).format(value)
}

const expanded = ref(new Set<string>())
const keyOf = (group: ReportGroup) => group.id ?? group.name ?? ''

function toggle(group: ReportGroup) {
  const key = keyOf(group)
  const next = new Set(expanded.value)
  if (next.has(key)) next.delete(key)
  else next.add(key)
  expanded.value = next
}

// A new grouping is a new list: what was open no longer means anything.
watch(groupBy, () => (expanded.value = new Set()))
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
    <span class="skeleton" aria-hidden="true" style="width: 30%" />
    <span class="skeleton" aria-hidden="true" style="width: 70%" />
    <span class="skeleton" aria-hidden="true" style="width: 50%" />
  </div>

  <div v-else class="summary" :data-loading="loading ? '' : undefined" :aria-busy="loading">
    <div v-if="error" class="alert" role="alert">
      <span>{{ t('reports.loadFailed') }} {{ error }}</span>
      <UiButton size="sm" @click="load">{{ t('common.retry') }}</UiButton>
    </div>

    <section class="sheet overview" :aria-label="t('reports.totals.label')">
      <dl class="totals">
        <div class="total-main">
          <dt>{{ t('reports.totals.total') }}</dt>
          <dd class="figure">{{ duration(data.totals.duration) }}</dd>
        </div>
        <div>
          <dt>{{ t('reports.totals.billable') }}</dt>
          <dd class="num">{{ duration(data.totals.billable_duration) }}</dd>
        </div>
        <div v-if="priced">
          <dt>{{ t('reports.totals.amount') }}</dt>
          <dd class="num">{{ money(data.totals.amount) }}</dd>
        </div>
        <div>
          <dt>{{ t('reports.totals.entries') }}</dt>
          <dd class="num">{{ data.totals.entries }}</dd>
        </div>
      </dl>

      <DayChart v-if="data.by_day && data.totals.duration > 0" :days="data.by_day" :money="money" />
    </section>

    <section class="sheet groups" :aria-label="t('reports.group.label')">
      <header class="groups-head">
        <UiSegmented v-model="groupBy" :options="groupOptions" :label="t('reports.group.label')" />
        <span class="then muted">{{ t('reports.group.then') }}</span>
        <UiCombobox
          v-model="subgroupBy"
          :items="subgroupItems"
          :label="t('reports.group.subgroupLabel')"
          :placeholder="t('reports.group.none')"
          :none-label="t('reports.group.none')"
          compact
        />
      </header>

      <p v-if="!data.groups.length" class="empty muted">{{ t('reports.empty') }}</p>

      <table v-else class="data-table group-table">
        <thead>
          <tr>
            <th scope="col">{{ t(`reports.group.${groupBy}`) }}</th>
            <th scope="col" class="share-col">{{ t('reports.share') }}</th>
            <th scope="col" class="num-col">{{ t('reports.duration') }}</th>
            <th v-if="priced" scope="col" class="num-col">{{ t('reports.totals.amount') }}</th>
          </tr>
        </thead>
        <tbody v-for="group in data.groups" :key="keyOf(group)">
          <tr class="group-row">
            <td>
              <button
                v-if="group.subgroups.length"
                type="button"
                class="group-name"
                :aria-expanded="expanded.has(keyOf(group))"
                @click="toggle(group)"
              >
                <AppIcon
                  :name="expanded.has(keyOf(group)) ? 'chevron-down' : 'chevron-right'"
                  :size="16"
                />
                <span
                  v-if="groupBy === 'project'"
                  class="row-dot"
                  :style="{ background: group.color ?? 'transparent' }"
                  :data-none="group.color ? undefined : ''"
                />
                <span class="name" :data-none="group.name === null ? '' : undefined">{{
                  nameOf(group, groupBy)
                }}</span>
                <span v-if="group.client_name" class="client muted">{{ group.client_name }}</span>
              </button>
              <span v-else class="group-name">
                <span
                  v-if="groupBy === 'project'"
                  class="row-dot"
                  :style="{ background: group.color ?? 'transparent' }"
                  :data-none="group.color ? undefined : ''"
                />
                <span class="name" :data-none="group.name === null ? '' : undefined">{{
                  nameOf(group, groupBy)
                }}</span>
                <span v-if="group.client_name" class="client muted">{{ group.client_name }}</span>
              </span>
            </td>
            <td class="share-col">
              <span class="share">
                <span class="share-track"
                  ><span class="share-bar" :style="{ width: `${share(group) * 100}%` }"
                /></span>
                <span class="share-value num">{{ percent(share(group)) }}</span>
              </span>
            </td>
            <td class="num-col num strong">{{ duration(group.duration) }}</td>
            <td v-if="priced" class="num-col num">
              {{ group.amount !== '0.00' ? money(group.amount) : '' }}
            </td>
          </tr>
          <template v-if="expanded.has(keyOf(group)) && subgroupBy">
            <tr v-for="sub in group.subgroups" :key="keyOf(sub)" class="sub-row">
              <td>
                <span class="group-name sub">
                  <span
                    v-if="subgroupBy === 'project'"
                    class="row-dot"
                    :style="{ background: sub.color ?? 'transparent' }"
                    :data-none="sub.color ? undefined : ''"
                  />
                  <span class="name" :data-none="sub.name === null ? '' : undefined">{{
                    nameOf(sub, subgroupBy)
                  }}</span>
                </span>
              </td>
              <td class="share-col">
                <span class="share">
                  <span class="share-track"
                    ><span class="share-bar quiet" :style="{ width: `${share(sub) * 100}%` }"
                  /></span>
                  <span class="share-value num">{{ percent(share(sub)) }}</span>
                </span>
              </td>
              <td class="num-col num">{{ duration(sub.duration) }}</td>
              <td v-if="priced" class="num-col num">
                {{ sub.amount !== '0.00' ? money(sub.amount) : '' }}
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </section>
  </div>
</template>

<style scoped>
.summary {
  display: flex;
  flex-direction: column;
  gap: 16px;
  transition: opacity var(--dur) var(--ease);
}

/* Refetch keeps the frame: the old report dims instead of turning into skeletons. */
.summary[data-loading] {
  opacity: 0.55;
}

.skeleton-sheet {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 24px;
}

.overview {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 20px 20px 16px;
}

/* The period total is the one loud figure of the page, printed like the
   timer's clock; the rest are quiet pencil-and-ink pairs beside it. */
.totals {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 12px 40px;
  margin: 0;
}

.totals dt {
  color: var(--text-muted);
  font-size: var(--text-xs);
}

.totals dd {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: 500;
}

.total-main {
  margin-right: 16px;
}

.totals .figure {
  font-size: var(--text-clock);
  font-weight: 600;
  line-height: 1.1;
  /* Sharp printed digits like .num, but proportional: a lone large number
     looks loose in tabular figures. */
  font-variation-settings: 'SHRP' 100;
}

.groups {
  overflow: hidden;
}

.groups-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 12px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
}

.then {
  font-size: var(--text-xs);
}

.empty {
  padding: 32px 16px;
  text-align: center;
}

.group-table td {
  padding-block: 6px;
}

.group-name {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 32px;
  max-width: 100%;
  padding: 0;
  border: 0;
  background: none;
  color: var(--text);
  font: inherit;
  font-weight: 500;
  text-align: left;
}

button.group-name {
  cursor: pointer;
}

button.group-name > svg {
  flex: 0 0 auto;
  color: var(--text-muted);
}

/* Subgroups line up under the group name, past its chevron. */
.group-name.sub {
  padding-left: 24px;
  font-weight: 400;
}

.name {
  min-width: 0;
  overflow-wrap: anywhere;
}

.name[data-none] {
  color: var(--text-muted);
  font-weight: 400;
}

.row-dot[data-none] {
  border: 1.5px solid var(--control-border);
}

.client {
  font-weight: 400;
  white-space: nowrap;
}

.share-col {
  width: 28%;
}

.share {
  display: flex;
  align-items: center;
  gap: 10px;
}

.share-track {
  flex: 1 1 auto;
  height: 8px;
}

.share-bar {
  display: block;
  height: 100%;
  min-width: 2px;
  border-radius: 0 4px 4px 0;
  background: var(--accent);
}

.share-bar.quiet {
  background: var(--chart-quiet);
}

.share-value {
  flex: 0 0 4.5ch;
  color: var(--text-muted);
  font-size: var(--text-xs);
  text-align: right;
}

.strong {
  color: var(--text);
  font-weight: 500;
}

.sub-row td {
  border-top-color: transparent;
}

.sub-row .num-col.num {
  color: var(--text-muted);
}

@media (width < 700px) {
  .share-col {
    display: none;
  }

  .totals {
    gap: 12px 24px;
  }

  .total-main {
    flex-basis: 100%;
  }
}
</style>
