<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { DateValue } from '@internationalized/date'
import { parseDate } from '@internationalized/date'
import {
  CalendarCell,
  CalendarCellTrigger,
  CalendarGrid,
  CalendarGridBody,
  CalendarGridHead,
  CalendarGridRow,
  CalendarHeadCell,
  CalendarHeader,
  CalendarHeading,
  CalendarNext,
  CalendarPrev,
  CalendarRoot,
} from 'reka-ui'

import AppIcon from '@/components/AppIcon.vue'
import { usePreferencesStore } from '@/stores/preferences'
import { weekOf } from '@/utils/period'

/**
 * A month with the shown week marked across its row, so it is plain which
 * week of the month it is. A click on any day picks that day's week; the
 * caller aligns it to the first day of the week.
 */
const props = defineProps<{ date: string }>()
const emit = defineEmits<{ select: [string] }>()

const { t, locale } = useI18n()
const preferences = usePreferencesStore()

const week = computed(() => weekOf(props.date, preferences.weekStart))
const placeholder = parseDate(props.date)
const weekStartsOn = computed(() => preferences.weekStart as 0 | 1 | 2 | 3 | 4 | 5 | 6)

function marks(day: DateValue) {
  const key = day.toString()
  const { from, to } = week.value
  if (key < from || key > to) return {}
  return {
    'data-in-week': '',
    'data-week-start': key === from ? '' : undefined,
    'data-week-end': key === to ? '' : undefined,
  }
}

function pick(value: DateValue | undefined) {
  if (value) emit('select', value.toString())
}
</script>

<template>
  <CalendarRoot
    v-slot="{ weekDays, grid }"
    class="ui-week-calendar"
    :default-placeholder="placeholder"
    :locale="locale"
    :week-starts-on="weekStartsOn"
    weekday-format="short"
    fixed-weeks
    @update:model-value="pick"
  >
    <CalendarHeader class="ui-calendar-header">
      <CalendarPrev class="ui-calendar-nav" :aria-label="t('datePicker.previous')">
        <AppIcon name="chevron-left" :size="16" />
      </CalendarPrev>
      <CalendarHeading class="ui-calendar-heading" />
      <CalendarNext class="ui-calendar-nav" :aria-label="t('datePicker.next')">
        <AppIcon name="chevron-right" :size="16" />
      </CalendarNext>
    </CalendarHeader>

    <CalendarGrid v-for="month in grid" :key="month.value.toString()" class="ui-calendar-grid">
      <CalendarGridHead>
        <CalendarGridRow class="ui-calendar-row">
          <CalendarHeadCell v-for="day in weekDays" :key="day" class="ui-calendar-weekday">
            {{ day }}
          </CalendarHeadCell>
        </CalendarGridRow>
      </CalendarGridHead>
      <CalendarGridBody>
        <CalendarGridRow v-for="(row, index) in month.rows" :key="index" class="ui-calendar-row">
          <CalendarCell v-for="day in row" :key="day.toString()" :date="day">
            <CalendarCellTrigger
              :day="day"
              :month="month.value"
              class="ui-calendar-day num"
              v-bind="marks(day)"
            />
          </CalendarCell>
        </CalendarGridRow>
      </CalendarGridBody>
    </CalendarGrid>
  </CalendarRoot>
</template>
