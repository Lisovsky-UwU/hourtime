<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { DateRange } from 'reka-ui'
import { parseDate, today, getLocalTimeZone } from '@internationalized/date'
import {
  RangeCalendarCell,
  RangeCalendarCellTrigger,
  RangeCalendarGrid,
  RangeCalendarGridBody,
  RangeCalendarGridHead,
  RangeCalendarGridRow,
  RangeCalendarHeadCell,
  RangeCalendarHeader,
  RangeCalendarHeading,
  RangeCalendarNext,
  RangeCalendarPrev,
  RangeCalendarRoot,
} from 'reka-ui'

import AppIcon from '@/components/AppIcon.vue'
import { usePreferencesStore } from '@/stores/preferences'
import type { Period } from '@/utils/period'

/**
 * A date range on one month calendar: the first click is the start, the
 * second the end. `select` fires once both ends are picked; the range shown
 * at first is `initial`, read when the calendar mounts.
 */
const props = defineProps<{ initial: Period | null }>()
const emit = defineEmits<{ select: [Period] }>()

const { t, locale } = useI18n()
const preferences = usePreferencesStore()

const defaultValue = computed<DateRange>(() =>
  props.initial
    ? { start: parseDate(props.initial.from), end: parseDate(props.initial.to) }
    : { start: undefined, end: undefined },
)
const placeholder = props.initial ? parseDate(props.initial.from) : today(getLocalTimeZone())
const weekStartsOn = computed(() => preferences.weekStart as 0 | 1 | 2 | 3 | 4 | 5 | 6)

function onValid(range: DateRange) {
  if (range.start && range.end) {
    emit('select', { from: range.start.toString(), to: range.end.toString() })
  }
}
</script>

<template>
  <RangeCalendarRoot
    v-slot="{ weekDays, grid }"
    class="ui-range-calendar"
    :default-value="defaultValue"
    :default-placeholder="placeholder"
    :locale="locale"
    :week-starts-on="weekStartsOn"
    weekday-format="short"
    fixed-weeks
    @update:valid-model-value="onValid"
  >
    <RangeCalendarHeader class="ui-calendar-header">
      <RangeCalendarPrev class="ui-calendar-nav" :aria-label="t('datePicker.previous')">
        <AppIcon name="chevron-left" :size="16" />
      </RangeCalendarPrev>
      <RangeCalendarHeading class="ui-calendar-heading" />
      <RangeCalendarNext class="ui-calendar-nav" :aria-label="t('datePicker.next')">
        <AppIcon name="chevron-right" :size="16" />
      </RangeCalendarNext>
    </RangeCalendarHeader>

    <RangeCalendarGrid v-for="month in grid" :key="month.value.toString()" class="ui-calendar-grid">
      <RangeCalendarGridHead>
        <RangeCalendarGridRow class="ui-calendar-row">
          <RangeCalendarHeadCell v-for="day in weekDays" :key="day" class="ui-calendar-weekday">
            {{ day }}
          </RangeCalendarHeadCell>
        </RangeCalendarGridRow>
      </RangeCalendarGridHead>
      <RangeCalendarGridBody>
        <RangeCalendarGridRow
          v-for="(week, index) in month.rows"
          :key="index"
          class="ui-calendar-row"
        >
          <RangeCalendarCell v-for="day in week" :key="day.toString()" :date="day">
            <RangeCalendarCellTrigger :day="day" :month="month.value" class="ui-calendar-day num" />
          </RangeCalendarCell>
        </RangeCalendarGridRow>
      </RangeCalendarGridBody>
    </RangeCalendarGrid>
  </RangeCalendarRoot>
</template>
