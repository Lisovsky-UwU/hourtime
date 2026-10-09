<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  ListboxContent,
  ListboxFilter,
  ListboxGroup,
  ListboxGroupLabel,
  ListboxItem,
  ListboxItemIndicator,
  ListboxRoot,
  PopoverContent,
  PopoverPortal,
  PopoverRoot,
  PopoverTrigger,
} from 'reka-ui'

import AppIcon from '@/components/AppIcon.vue'
import type { ComboboxItem } from '@/components/ui/UiCombobox.vue'
import { NONE } from '@/composables/useReportQuery'

/**
 * One filter of the report bar: projects, clients, tags or billable.
 *
 * The trigger is pencil while the filter is off and ink with the number of
 * picked values while it is on - the same "state is ink" rule as tags and
 * billable in the entry rows. Ticks change a draft that is applied once, when
 * the list closes, so picking five projects reloads the report once.
 */
const model = defineModel<string[]>({ required: true })

const props = withDefaults(
  defineProps<{
    label: string
    items: ComboboxItem[]
    /** An extra first item meaning "without one", stored as NONE. */
    noneLabel?: string
    /** One value at most; picking the current one again clears the filter. */
    single?: boolean
  }>(),
  { noneLabel: undefined, single: false },
)

const { t } = useI18n()

const open = ref(false)
const query = ref('')
const draft = ref<string[]>([])

watch(open, (value) => {
  if (value) {
    draft.value = [...model.value]
    return
  }
  query.value = ''
  const changed =
    draft.value.length !== model.value.length || draft.value.some((id) => !model.value.includes(id))
  if (changed) model.value = [...draft.value]
})

const searchable = computed(() => props.items.length > 7)
const normalizedQuery = computed(() => query.value.trim().toLocaleLowerCase())

const sections = computed(() => {
  const matches = normalizedQuery.value
    ? props.items.filter((item) => item.label.toLocaleLowerCase().includes(normalizedQuery.value))
    : props.items
  const groups = new Map<string, ComboboxItem[]>()
  for (const item of matches) {
    const key = item.group ?? ''
    groups.set(key, [...(groups.get(key) ?? []), item])
  }
  return [...groups.entries()]
    .sort(([a], [b]) => (a === '' ? -1 : b === '' ? 1 : 0))
    .map(([label, items]) => ({ label, items }))
})

const showNone = computed(() => props.noneLabel !== undefined && normalizedQuery.value === '')

function select(values: unknown) {
  if (props.single) {
    const value = typeof values === 'string' ? values : null
    draft.value = value ? [value] : []
    open.value = false
    return
  }
  draft.value = Array.isArray(values)
    ? values.filter((v): v is string => typeof v === 'string')
    : []
}

/** "Projects" when off, "hourtime" for one value, "Projects 3" for several. */
const summary = computed(() => {
  if (model.value.length !== 1) return props.label
  const value = model.value[0]
  if (value === NONE) return props.noneLabel ?? props.label
  return props.items.find((item) => item.value === value)?.label ?? props.label
})

const accessibleName = computed(() =>
  model.value.length
    ? `${props.label}: ${t('reports.filters.picked', model.value.length)}`
    : props.label,
)
</script>

<template>
  <PopoverRoot v-model:open="open">
    <PopoverTrigger as-child>
      <button
        type="button"
        class="filter-trigger"
        :data-active="model.length ? '' : undefined"
        :aria-label="accessibleName"
      >
        <span class="filter-value">{{ summary }}</span>
        <span v-if="model.length > 1" class="filter-count num">{{ model.length }}</span>
        <AppIcon name="chevron-down" :size="14" />
      </button>
    </PopoverTrigger>

    <PopoverPortal>
      <PopoverContent
        class="ui-floating ui-combobox"
        align="start"
        :side-offset="6"
        :collision-padding="8"
      >
        <ListboxRoot
          :model-value="single ? (draft[0] ?? undefined) : draft"
          :multiple="!single"
          selection-behavior="toggle"
          highlight-on-hover
          @update:model-value="select"
        >
          <div v-if="searchable" class="ui-combobox-search">
            <AppIcon name="search" :size="16" />
            <ListboxFilter
              v-model="query"
              auto-focus
              class="ui-combobox-input"
              :placeholder="t('ui.search')"
              :aria-label="t('ui.search')"
            />
          </div>

          <ListboxContent class="ui-combobox-list">
            <ListboxItem v-if="showNone" :value="NONE" class="ui-menu-item">
              <span class="box" aria-hidden="true">
                <ListboxItemIndicator class="box-check"
                  ><AppIcon name="check" :size="14"
                /></ListboxItemIndicator>
              </span>
              <span class="ui-combobox-label muted">{{ noneLabel }}</span>
            </ListboxItem>

            <ListboxGroup
              v-for="section in sections"
              :key="section.label"
              class="ui-combobox-group"
            >
              <ListboxGroupLabel v-if="section.label" class="ui-combobox-group-label">
                {{ section.label }}
              </ListboxGroupLabel>
              <ListboxItem
                v-for="item in section.items"
                :key="item.value"
                :value="item.value"
                class="ui-menu-item"
              >
                <span class="box" aria-hidden="true">
                  <ListboxItemIndicator class="box-check"
                    ><AppIcon name="check" :size="14"
                  /></ListboxItemIndicator>
                </span>
                <span
                  v-if="item.color"
                  class="ui-combobox-dot"
                  :style="{ background: item.color }"
                />
                <span class="ui-combobox-label">{{ item.label }}</span>
              </ListboxItem>
            </ListboxGroup>

            <p v-if="!sections.length && !showNone" class="ui-combobox-empty">
              {{ t('ui.noResults') }}
            </p>
          </ListboxContent>
        </ListboxRoot>
      </PopoverContent>
    </PopoverPortal>
  </PopoverRoot>
</template>

<style scoped>
.filter-trigger {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  max-width: 220px;
  height: var(--control-h);
  padding: 0 8px 0 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: transparent;
  color: var(--text-muted);
  font: inherit;
  cursor: pointer;
  transition:
    background-color var(--dur) var(--ease),
    border-color var(--dur) var(--ease);
}

.filter-trigger:hover,
.filter-trigger[data-state='open'] {
  background: var(--surface-muted);
}

/* On: ink on the sheet color with the field border, so the bar shows at a
   glance which filters narrow the report. */
.filter-trigger[data-active] {
  border-color: var(--control-border);
  background: var(--surface);
  color: var(--text);
  font-weight: 500;
}

.filter-trigger > svg {
  flex: 0 0 auto;
  color: var(--text-muted);
}

.filter-value {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.filter-count {
  min-width: 18px;
  padding: 0 5px;
  border-radius: var(--radius-full);
  background: var(--accent-soft);
  color: var(--accent);
  font-size: var(--text-xs);
  font-weight: 600;
  text-align: center;
}
</style>
