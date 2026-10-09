<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import AppIcon from '@/components/AppIcon.vue'
import DetailedReport from '@/components/reports/DetailedReport.vue'
import FilterSelect from '@/components/reports/FilterSelect.vue'
import PeriodPicker from '@/components/reports/PeriodPicker.vue'
import SummaryReport from '@/components/reports/SummaryReport.vue'
import WeeklyReport from '@/components/reports/WeeklyReport.vue'
import UiButton from '@/components/ui/UiButton.vue'
import type { ComboboxItem } from '@/components/ui/UiCombobox.vue'
import { useReportQuery } from '@/composables/useReportQuery'
import type { ReportView } from '@/composables/useReportQuery'
import { useClientsStore } from '@/stores/clients'
import { useProjectsStore } from '@/stores/projects'
import { useTagsStore } from '@/stores/tags'
import type { Period } from '@/utils/period'

/**
 * Reports: one filter row scopes all three views, and the whole report lives
 * in the URL (see useReportQuery), so switching views keeps the filters.
 */
const { t } = useI18n()
const report = useReportQuery()
const projects = useProjectsStore()
const clients = useClientsStore()
const tags = useTagsStore()

const views: ReportView[] = ['summary', 'detailed', 'weekly']

const period = computed({
  get: () => report.state.value.period,
  set: (value: Period | null) => report.setPeriod(value),
})

const projectItems = computed<ComboboxItem[]>(() =>
  [...projects.items]
    .sort((a, b) => Number(a.archived) - Number(b.archived) || a.name.localeCompare(b.name))
    .map((project) => ({
      value: project.id,
      label: project.name,
      color: project.color,
      group: clients.find(project.client_id)?.name,
    })),
)

const clientItems = computed<ComboboxItem[]>(() =>
  [...clients.items]
    .sort((a, b) => a.name.localeCompare(b.name))
    .map((client) => ({ value: client.id, label: client.name })),
)

const tagItems = computed<ComboboxItem[]>(() =>
  tags.sorted.map((tag) => ({ value: tag.id, label: tag.name })),
)

const billableItems = computed<ComboboxItem[]>(() => [
  { value: 'yes', label: t('billing.billable') },
  { value: 'no', label: t('billing.notBillable') },
])

function listModel(key: 'projects' | 'clients' | 'tags', param: string) {
  return computed({
    get: () => report.state.value[key],
    set: (value: string[]) => report.patch({ [param]: value }),
  })
}

const pickedProjects = listModel('projects', 'project')
const pickedClients = listModel('clients', 'client')
const pickedTags = listModel('tags', 'tag')

const pickedBillable = computed({
  get: () => (report.state.value.billable ? [report.state.value.billable] : []),
  set: (value: string[]) => report.patch({ billable: value[0] ?? null }),
})

// The search box writes to the URL after a pause, not on every key.
const description = ref(report.state.value.description)
let typing: number | null = null

watch(description, (value) => {
  if (typing !== null) window.clearTimeout(typing)
  typing = window.setTimeout(() => {
    typing = null
    report.patch({ q: value.trim() })
  }, 350)
})

// Back/forward and "Clear filters" change the URL under the box.
watch(
  () => report.state.value.description,
  (value) => {
    if (typing === null && value !== description.value.trim()) description.value = value
  },
)

onUnmounted(() => {
  if (typing !== null) window.clearTimeout(typing)
})

function clear() {
  if (typing !== null) window.clearTimeout(typing)
  typing = null
  description.value = ''
  report.clearFilters()
}
</script>

<template>
  <div class="reports-page">
    <header class="reports-head">
      <h1>{{ t('reports.title') }}</h1>
      <nav class="views" :aria-label="t('reports.views')">
        <RouterLink
          v-for="view in views"
          :key="view"
          :to="report.viewLink(view)"
          class="view-link"
          :aria-current="report.view.value === view ? 'page' : undefined"
        >
          {{ t(`reports.view.${view}`) }}
        </RouterLink>
      </nav>
    </header>

    <div class="filters" role="group" :aria-label="t('reports.filters.label')">
      <PeriodPicker
        v-model="period"
        :allow-all="report.view.value !== 'weekly'"
        :weeks="report.view.value === 'weekly'"
      />

      <span class="filters-sep" aria-hidden="true" />

      <FilterSelect
        v-model="pickedProjects"
        :label="t('reports.filters.projects')"
        :items="projectItems"
        :none-label="t('reports.without.project')"
      />
      <FilterSelect
        v-model="pickedClients"
        :label="t('reports.filters.clients')"
        :items="clientItems"
        :none-label="t('reports.without.client')"
      />
      <FilterSelect
        v-model="pickedTags"
        :label="t('reports.filters.tags')"
        :items="tagItems"
        :none-label="t('reports.without.tag')"
      />
      <FilterSelect
        v-model="pickedBillable"
        :label="t('reports.filters.billable')"
        :items="billableItems"
        single
      />

      <label class="search">
        <AppIcon name="search" :size="16" />
        <span class="visually-hidden">{{ t('reports.filters.description') }}</span>
        <input
          v-model="description"
          type="search"
          :placeholder="t('reports.filters.description')"
        />
      </label>

      <UiButton v-if="report.filtered.value" variant="ghost" size="sm" icon="close" @click="clear">
        {{ t('reports.filters.clear') }}
      </UiButton>
    </div>

    <SummaryReport v-if="report.view.value === 'summary'" />
    <DetailedReport v-else-if="report.view.value === 'detailed'" />
    <WeeklyReport v-else />
  </div>
</template>

<style scoped>
.reports-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: var(--page-width-wide);
  margin: 0 auto;
  padding: 28px 24px 64px;
}

.reports-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px 24px;
}

/* Views look like the segmented control but are links: each has its own URL. */
.views {
  display: inline-flex;
  padding: 2px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--surface-muted);
}

.view-link {
  display: inline-flex;
  align-items: center;
  height: calc(var(--control-h) - 6px);
  padding: 0 14px;
  border-radius: var(--radius-sm);
  color: var(--text-muted);
  font-weight: 500;
  text-decoration: none;
  white-space: nowrap;
  transition:
    background-color var(--dur) var(--ease),
    color var(--dur) var(--ease);
}

.view-link:hover {
  color: var(--text);
}

.view-link[aria-current='page'] {
  background: var(--surface);
  color: var(--text);
  outline: 1px solid var(--border-strong);
  outline-offset: -1px;
}

.view-link:focus-visible {
  outline: 2px solid var(--focus);
  outline-offset: -2px;
}

.filters {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.filters-sep {
  width: 1px;
  height: 20px;
  margin: 0 4px;
  background: var(--border);
}

.search {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex: 0 1 240px;
  min-width: 160px;
  height: var(--control-h);
  padding: 0 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text-muted);
}

.search:focus-within {
  border-color: var(--control-border);
  background: var(--surface);
  outline: 2px solid var(--focus);
  outline-offset: -1px;
}

.search input {
  flex: 1 1 auto;
  min-width: 0;
  border: 0;
  background: none;
  color: var(--text);
  font: inherit;
  outline: none;
}

.search input::placeholder {
  color: var(--text-muted);
  opacity: 1;
}

@media (width < 768px) {
  .reports-page {
    padding: 16px 16px 48px;
  }

  .filters-sep {
    display: none;
  }

  .search {
    flex: 1 1 100%;
  }
}
</style>
