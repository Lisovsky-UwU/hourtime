<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { DateValue } from '@internationalized/date'
import { parseDate } from '@internationalized/date'
import {
  DatePickerCalendar,
  DatePickerCell,
  DatePickerCellTrigger,
  DatePickerContent,
  DatePickerField,
  DatePickerGrid,
  DatePickerGridBody,
  DatePickerGridHead,
  DatePickerGridRow,
  DatePickerHeadCell,
  DatePickerHeader,
  DatePickerHeading,
  DatePickerInput,
  DatePickerNext,
  DatePickerPrev,
  DatePickerRoot,
  DatePickerTrigger,
} from 'reka-ui'

import AppIcon from '@/components/AppIcon.vue'
import { usePreferencesStore } from '@/stores/preferences'

/**
 * A date you can type segment by segment or pick from a calendar. The model is
 * `YYYY-MM-DD` (empty when unset), the same string the rest of the app uses.
 * `change` fires after the model on every user edit, so callers can save
 * without watching a value they also write themselves.
 */
const model = defineModel<string>({ required: true })
const open = defineModel<boolean>('open', { default: false })

const props = defineProps<{
  label: string
  /** Earliest allowed date, `YYYY-MM-DD`. */
  min?: string
}>()
const emit = defineEmits<{ change: [string] }>()

const { t, locale } = useI18n()
const preferences = usePreferencesStore()

function toDate(value: string | undefined): DateValue | undefined {
  if (!value) return undefined
  try {
    return parseDate(value)
  } catch {
    return undefined
  }
}

const value = computed(() => toDate(model.value) ?? null)
const minValue = computed(() => toDate(props.min))
// Our `weekStart` is numbered like `getDay()`, which is what reka expects too.
const weekStartsOn = computed(() => preferences.weekStart as 0 | 1 | 2 | 3 | 4 | 5 | 6)

function update(date: DateValue | undefined) {
  model.value = date?.toString() ?? ''
  emit('change', model.value)
}
</script>

<template>
  <div class="ui-date">
    <DatePickerRoot
      v-model:open="open"
      :model-value="value"
      :min-value="minValue"
      :locale="locale"
      :week-starts-on="weekStartsOn"
      weekday-format="short"
      fixed-weeks
      close-on-select
      @update:model-value="update"
    >
      <DatePickerField v-slot="{ segments }" class="ui-date-field num" :aria-label="label">
        <template v-for="item in segments" :key="item.part">
          <DatePickerInput v-if="item.part === 'literal'" :part="item.part" class="ui-date-literal">
            {{ item.value }}
          </DatePickerInput>
          <DatePickerInput v-else :part="item.part" class="ui-date-segment">
            {{ item.value }}
          </DatePickerInput>
        </template>
        <DatePickerTrigger class="ui-date-trigger" :aria-label="t('datePicker.open')">
          <AppIcon name="calendar" :size="14" />
        </DatePickerTrigger>
      </DatePickerField>

      <DatePickerContent
        class="ui-floating ui-calendar"
        align="start"
        :side-offset="6"
        :collision-padding="8"
      >
        <DatePickerCalendar v-slot="{ weekDays, grid }">
          <DatePickerHeader class="ui-calendar-header">
            <DatePickerPrev class="ui-calendar-nav" :aria-label="t('datePicker.previous')">
              <AppIcon name="chevron-left" :size="16" />
            </DatePickerPrev>
            <DatePickerHeading class="ui-calendar-heading" />
            <DatePickerNext class="ui-calendar-nav" :aria-label="t('datePicker.next')">
              <AppIcon name="chevron-right" :size="16" />
            </DatePickerNext>
          </DatePickerHeader>

          <DatePickerGrid v-for="month in grid" :key="month.value.toString()" class="ui-calendar-grid">
            <DatePickerGridHead>
              <DatePickerGridRow class="ui-calendar-row">
                <DatePickerHeadCell v-for="day in weekDays" :key="day" class="ui-calendar-weekday">
                  {{ day }}
                </DatePickerHeadCell>
              </DatePickerGridRow>
            </DatePickerGridHead>
            <DatePickerGridBody>
              <DatePickerGridRow
                v-for="(week, index) in month.rows"
                :key="index"
                class="ui-calendar-row"
              >
                <DatePickerCell v-for="day in week" :key="day.toString()" :date="day">
                  <DatePickerCellTrigger :day="day" :month="month.value" class="ui-calendar-day num" />
                </DatePickerCell>
              </DatePickerGridRow>
            </DatePickerGridBody>
          </DatePickerGrid>
        </DatePickerCalendar>
      </DatePickerContent>
    </DatePickerRoot>
  </div>
</template>

<style>
/* Global: the calendar renders in a portal. The field's look sits under
   :where() so a parent's own class restyles it without a specificity fight. */
:where(.ui-date) {
  display: inline-flex;
  align-items: center;
  height: var(--control-h-sm);
  padding: 0 2px 0 6px;
  border: 1px solid var(--control-border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text);
  font-size: var(--text-sm);
}

.ui-date:focus-within {
  outline: 2px solid var(--focus);
  outline-offset: -1px;
}

.ui-date-field {
  display: inline-flex;
  align-items: center;
  height: 100%;
  font-variant-numeric: tabular-nums;
}

.ui-date-segment {
  padding: 0 1px;
  border-radius: 3px;
  caret-color: transparent;
  outline: none;
}

.ui-date-segment[data-placeholder] {
  color: var(--text-muted);
}

.ui-date-segment:focus {
  background: var(--accent-soft);
  color: var(--text);
}

.ui-date-literal {
  color: var(--text-muted);
}

.ui-date-trigger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  margin-left: 4px;
  padding: 0;
  border: 0;
  border-radius: var(--radius-sm);
  background: none;
  color: var(--text-muted);
  cursor: pointer;
}

.ui-date-trigger:hover,
.ui-date-trigger[data-state='open'] {
  background: var(--surface-muted);
  color: var(--text);
}

.ui-date-trigger:focus-visible {
  outline: 2px solid var(--focus);
  outline-offset: -2px;
}

.ui-floating.ui-calendar {
  min-width: 0;
  padding: 10px;
}

.ui-calendar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.ui-calendar-heading {
  font-weight: 600;
}

/* Russian month names come lowercase from Intl. */
.ui-calendar-heading::first-letter {
  text-transform: uppercase;
}

.ui-calendar-nav {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  padding: 0;
  border: 0;
  border-radius: var(--radius-sm);
  background: none;
  color: var(--text-muted);
  cursor: pointer;
}

.ui-calendar-nav:hover {
  background: var(--surface-muted);
  color: var(--text);
}

.ui-calendar-nav:focus-visible,
.ui-calendar-day:focus-visible {
  outline: 2px solid var(--focus);
  outline-offset: -2px;
}

.ui-calendar-grid {
  border-collapse: collapse;
}

.ui-calendar-weekday {
  width: 34px;
  height: 28px;
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-weight: 400;
}

.ui-calendar-day {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 32px;
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  cursor: pointer;
  outline: none;
}

.ui-calendar-day:hover {
  background: var(--surface-muted);
}

.ui-calendar-day[data-outside-view] {
  color: var(--text-muted);
  opacity: 0.6;
}

/* Today keeps a quiet ring, so it still reads as today once selected elsewhere. */
.ui-calendar-day[data-today] {
  box-shadow: inset 0 0 0 1px var(--border-strong);
  font-weight: 600;
}

.ui-calendar-day[data-selected] {
  background: var(--accent);
  color: var(--accent-contrast);
  box-shadow: none;
}

.ui-calendar-day[data-disabled],
.ui-calendar-day[data-unavailable] {
  color: var(--text-muted);
  opacity: 0.4;
  pointer-events: none;
}

@media (width < 768px) {
  :where(.ui-date) {
    font-size: var(--text-md);
  }
}
</style>
