<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  ListboxContent,
  ListboxFilter,
  ListboxItem,
  ListboxItemIndicator,
  ListboxRoot,
  PopoverContent,
  PopoverPortal,
  PopoverRoot,
  PopoverTrigger,
} from 'reka-ui'

import AppIcon from '@/components/AppIcon.vue'

export interface ComboboxItem {
  value: string
  label: string
  /** Shown as a dot before the label, e.g. a project color. */
  color?: string
}

/**
 * A button that opens a searchable list, the way Toggl picks a project.
 *
 * Built on Popover + Listbox rather than reka's Combobox: the field stays a
 * compact button in the timer bar and the search box only exists while the
 * list is open.
 */
const model = defineModel<string | null>({ default: null })

const props = withDefaults(
  defineProps<{
    items: ComboboxItem[]
    /** Accessible name of the trigger, e.g. "Select project". */
    label: string
    /** Trigger text when nothing is selected. */
    placeholder: string
    /** Adds an item that clears the selection. */
    noneLabel?: string
    /** Offers "Create …" for a query that matches no item; emits `create`. */
    creatable?: boolean
    disabled?: boolean
    /** Smaller trigger for dense rows. */
    compact?: boolean
  }>(),
  { noneLabel: undefined, creatable: false, disabled: false, compact: false },
)

const emit = defineEmits<{ create: [name: string] }>()

const { t } = useI18n()

// Never a real id, so they cannot collide with item values.
const NONE = '\u0000none'
const CREATE = '\u0000create'

const open = ref(false)
const query = ref('')

watch(open, (value) => {
  if (!value) query.value = ''
})

const selected = computed(() => props.items.find((item) => item.value === model.value) ?? null)

const normalizedQuery = computed(() => query.value.trim().toLocaleLowerCase())

const filtered = computed(() =>
  normalizedQuery.value
    ? props.items.filter((item) => item.label.toLocaleLowerCase().includes(normalizedQuery.value))
    : props.items,
)

const canCreate = computed(
  () =>
    props.creatable &&
    normalizedQuery.value !== '' &&
    !props.items.some((item) => item.label.toLocaleLowerCase() === normalizedQuery.value),
)

const showNone = computed(() => props.noneLabel !== undefined && !normalizedQuery.value)

function choose(value: unknown) {
  if (value === CREATE) {
    emit('create', query.value.trim())
  } else if (typeof value === 'string') {
    model.value = value === NONE ? null : value
  }
  open.value = false
}
</script>

<template>
  <PopoverRoot v-model:open="open">
    <PopoverTrigger as-child>
      <button
        type="button"
        class="ui-combobox-trigger"
        :aria-label="`${label}: ${selected?.label ?? noneLabel ?? placeholder}`"
        :title="selected?.label"
        :disabled="disabled"
        :data-empty="selected ? undefined : ''"
        :data-compact="compact ? '' : undefined"
      >
        <span
          v-if="selected?.color"
          class="ui-combobox-dot"
          :style="{ background: selected.color }"
        />
        <span class="ui-combobox-value">{{ selected?.label ?? placeholder }}</span>
        <!-- A compact chip in a dense row reads as clickable without it. -->
        <AppIcon v-if="!compact" name="chevrons-up-down" :size="14" />
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
          :model-value="model ?? NONE"
          selection-behavior="replace"
          highlight-on-hover
          @update:model-value="choose"
        >
          <div class="ui-combobox-search">
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
              <span class="ui-combobox-dot is-none" />
              <span class="ui-combobox-label muted">{{ noneLabel }}</span>
              <ListboxItemIndicator class="ui-combobox-check">
                <AppIcon name="check" :size="16" />
              </ListboxItemIndicator>
            </ListboxItem>

            <ListboxItem
              v-for="item in filtered"
              :key="item.value"
              :value="item.value"
              class="ui-menu-item"
            >
              <span
                class="ui-combobox-dot"
                :class="{ 'is-none': !item.color }"
                :style="item.color ? { background: item.color } : undefined"
              />
              <span class="ui-combobox-label">{{ item.label }}</span>
              <ListboxItemIndicator class="ui-combobox-check">
                <AppIcon name="check" :size="16" />
              </ListboxItemIndicator>
            </ListboxItem>

            <ListboxItem v-if="canCreate" :value="CREATE" class="ui-menu-item ui-combobox-create">
              <AppIcon name="plus" :size="16" />
              <span class="ui-combobox-label">{{ t('ui.create', { name: query.trim() }) }}</span>
            </ListboxItem>

            <p v-if="!filtered.length && !canCreate && !showNone" class="ui-combobox-empty">
              {{ t('ui.noResults') }}
            </p>
          </ListboxContent>
        </ListboxRoot>
      </PopoverContent>
    </PopoverPortal>
  </PopoverRoot>
</template>

<style scoped>
.ui-combobox-trigger {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  max-width: 100%;
  height: var(--control-h);
  padding: 0 10px;
  border: 1px solid transparent;
  border-radius: var(--radius);
  background: transparent;
  color: var(--text);
  font: inherit;
  cursor: pointer;
  transition:
    background-color var(--dur) var(--ease),
    border-color var(--dur) var(--ease);
}

.ui-combobox-trigger:hover:not(:disabled),
.ui-combobox-trigger[data-state='open'] {
  background: var(--surface-muted);
}

.ui-combobox-trigger[data-compact] {
  height: var(--control-h-sm);
  gap: 6px;
  padding: 0 8px;
  border-radius: var(--radius-full);
}

/* No hover on touch screens: the chip shows its outline to read as a button. */
@media (hover: none) {
  .ui-combobox-trigger[data-compact] {
    border-color: var(--control-border);
  }
}

.ui-combobox-trigger[data-empty] {
  color: var(--text-muted);
}

.ui-combobox-trigger > svg {
  flex: 0 0 auto;
  color: var(--text-muted);
}

.ui-combobox-trigger:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.ui-combobox-value {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>

<style>
/* Global: the list lives in a portal. Doubled class: wins over .ui-floating
   whatever order the stylesheets load in. */
.ui-floating.ui-combobox {
  width: max(var(--reka-popover-trigger-width), 280px);
  max-width: calc(100vw - 16px);
  padding: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.ui-combobox-search {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 12px;
  border-bottom: 1px solid var(--border);
  color: var(--text-muted);
}

.ui-combobox-input {
  flex: 1;
  min-width: 0;
  height: 40px;
  border: 0;
  background: transparent;
  color: var(--text);
  font: inherit;
  outline: none;
}

.ui-combobox-input::placeholder {
  color: var(--text-muted);
}

.ui-combobox-list {
  max-height: min(320px, calc(var(--reka-popover-content-available-height) - 48px));
  overflow-y: auto;
  padding: 4px;
}

.ui-combobox-label {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ui-combobox-dot {
  flex: 0 0 auto;
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.ui-combobox-dot.is-none {
  border: 1.5px dashed var(--border-strong);
}

.ui-combobox-check {
  display: inline-flex;
  color: var(--accent);
}

.ui-combobox-create {
  color: var(--accent);
}

.ui-combobox-create > svg {
  color: inherit;
}

.ui-combobox-empty {
  padding: 12px 8px;
  color: var(--text-muted);
  text-align: center;
}

@media (width < 768px) {
  .ui-combobox-input {
    font-size: var(--text-md);
  }
}
</style>
