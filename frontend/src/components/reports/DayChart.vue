<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { useDuration } from '@/composables/useDuration'
import { usePreferencesStore } from '@/stores/preferences'
import type { ReportDay } from '@/types'
import { formatPeriod, parseDateKey, weekStartOf } from '@/utils/period'

/**
 * Time per day as columns: billable time in the accent at the base, the rest
 * stacked above it in a quiet gray. Long periods are bucketed by week or
 * month, so a column never gets thinner than a few pixels.
 *
 * Own SVG rather than a chart library: two kinds of mark do not justify a
 * dependency, and the marks follow the theme tokens directly.
 */
const props = defineProps<{
  days: ReportDay[]
  /** Amounts formatted for the tooltip; empty when the report has no money. */
  money: (amount: string) => string
}>()

const { t, d, locale } = useI18n()
const duration = useDuration()
const preferences = usePreferencesStore()

interface Bucket {
  key: string
  axis: string
  title: string
  duration: number
  billable: number
  amount: string
}

const unit = computed<'day' | 'week' | 'month'>(() =>
  props.days.length <= 62 ? 'day' : props.days.length <= 400 ? 'week' : 'month',
)

function sumAmounts(a: string, b: string): string {
  return ((Math.round(Number(a) * 100) + Math.round(Number(b) * 100)) / 100).toFixed(2)
}

const buckets = computed<Bucket[]>(() => {
  const result = new Map<string, Bucket>()
  for (const day of props.days) {
    const date = parseDateKey(day.date)
    let key = day.date
    let axis: string
    let title: string
    if (unit.value === 'day') {
      axis = d(date, props.days.length <= 7 ? 'axisWeekday' : 'axisDay')
      title = d(date, 'dayShort')
    } else if (unit.value === 'week') {
      key = weekStartOf(day.date, preferences.weekStart)
      axis = d(parseDateKey(key), 'axisDay')
      title = ''
    } else {
      key = day.date.slice(0, 7)
      axis = d(date, 'axisMonth')
      title = d(date, 'month')
    }
    const bucket = result.get(key)
    if (bucket) {
      bucket.duration += day.duration
      bucket.billable += day.billable_duration
      bucket.amount = sumAmounts(bucket.amount, day.amount)
      if (unit.value === 'week')
        bucket.title = formatPeriod({ from: key, to: day.date }, locale.value)
    } else {
      result.set(key, {
        key,
        axis,
        title:
          unit.value === 'week' ? formatPeriod({ from: key, to: day.date }, locale.value) : title,
        duration: day.duration,
        billable: day.billable_duration,
        amount: day.amount,
      })
    }
  }
  return [...result.values()]
})

// Layout. The width follows the sheet; the height is fixed so the page does
// not jump between periods.
const root = ref<HTMLElement | null>(null)
const width = ref(640)
const PLOT_H = 168
const AXIS_H = 24
const LEFT = 48
const TOP = 8

let observer: ResizeObserver | null = null
onMounted(() => {
  observer = new ResizeObserver(([entry]) => {
    if (entry) width.value = Math.max(240, entry.contentRect.width)
  })
  if (root.value) observer.observe(root.value)
})
onUnmounted(() => observer?.disconnect())

const HOUR = 3600
const STEPS = [0.25, 0.5, 1, 2, 3, 4, 6, 8, 12, 24, 48, 96, 168, 336, 720].map(
  (hours) => hours * HOUR,
)

/** Round gridlines: at most four steps above zero, each a whole number of hours where possible. */
const scale = computed(() => {
  const max = Math.max(...buckets.value.map((bucket) => bucket.duration), 0)
  const step = STEPS.find((candidate) => max / candidate <= 4) ?? Math.ceil(max / 4 / HOUR) * HOUR
  const top = Math.max(step, Math.ceil(max / step) * step)
  const ticks: number[] = []
  for (let value = 0; value <= top; value += step) ticks.push(value)
  return { top, ticks }
})

const plotW = computed(() => width.value - LEFT)
const band = computed(() => plotW.value / Math.max(1, buckets.value.length))
const barW = computed(() => Math.max(2, Math.min(24, band.value * 0.6)))

function y(seconds: number): number {
  return TOP + PLOT_H - (seconds / scale.value.top) * PLOT_H
}

/** A column with a 4px rounded top and a square foot on the baseline. */
function column(x: number, top: number, bottom: number, rounded: boolean): string {
  const w = barW.value
  const h = bottom - top
  if (h <= 0) return ''
  const r = rounded ? Math.min(4, w / 2, h) : 0
  return (
    `M${x},${bottom}V${top + r}` +
    (r
      ? `Q${x},${top} ${x + r},${top}H${x + w - r}Q${x + w},${top} ${x + w},${top + r}`
      : `H${x + w}`) +
    `V${bottom}Z`
  )
}

const GAP = 2

const marks = computed(() =>
  buckets.value.map((bucket, index) => {
    const x = LEFT + index * band.value + (band.value - barW.value) / 2
    const base = y(0)
    const billableTop = y(bucket.billable)
    const totalTop = y(bucket.duration)
    const rest = bucket.duration - bucket.billable
    return {
      bucket,
      index,
      x,
      billable: column(x, billableTop, base, rest <= 0),
      // The 2px gap in the sheet color separates the two parts of a column.
      rest:
        rest > 0 ? column(x, totalTop, bucket.billable > 0 ? billableTop - GAP : base, true) : '',
    }
  }),
)

/** Every label would collide on a month of days: keep every n-th. */
const labelEvery = computed(() => Math.max(1, Math.ceil(44 / band.value)))

const hasBillable = computed(() => buckets.value.some((bucket) => bucket.billable > 0))

const active = ref<number | null>(null)
const tooltip = computed(() => {
  if (active.value === null) return null
  const mark = marks.value[active.value]
  if (!mark) return null
  const left = Math.min(Math.max(mark.x + barW.value / 2, 90), width.value - 90)
  return { bucket: mark.bucket, left, top: y(mark.bucket.duration) }
})

function describe(bucket: Bucket): string {
  return `${bucket.title}: ${duration(bucket.duration)}`
}
</script>

<template>
  <figure ref="root" class="day-chart" :data-unit="unit">
    <figcaption class="legend">
      <span class="legend-title">{{ t(`reports.chart.per.${unit}`) }}</span>
      <template v-if="hasBillable">
        <span class="legend-key"><span class="swatch billable" />{{ t('billing.billable') }}</span>
        <span class="legend-key"><span class="swatch rest" />{{ t('billing.notBillable') }}</span>
      </template>
    </figcaption>

    <svg
      :width="width"
      :height="TOP + PLOT_H + AXIS_H"
      :viewBox="`0 0 ${width} ${TOP + PLOT_H + AXIS_H}`"
      aria-hidden="true"
      @pointerleave="active = null"
    >
      <g class="grid">
        <template v-for="tick in scale.ticks" :key="tick">
          <line :x1="LEFT" :x2="width" :y1="y(tick)" :y2="y(tick)" />
          <text
            :x="LEFT - 8"
            :y="y(tick)"
            class="tick num"
            text-anchor="end"
            dominant-baseline="middle"
          >
            {{ duration(tick) }}
          </text>
        </template>
      </g>

      <g
        v-for="mark in marks"
        :key="mark.bucket.key"
        :data-active="active === mark.index ? '' : undefined"
      >
        <path v-if="mark.billable" class="bar billable" :d="mark.billable" />
        <path v-if="mark.rest" class="bar rest" :d="mark.rest" />
        <text
          v-if="mark.index % labelEvery === 0"
          :x="mark.x + barW / 2"
          :y="TOP + PLOT_H + 16"
          class="tick num"
          text-anchor="middle"
        >
          {{ mark.bucket.axis }}
        </text>
        <!-- The hit area is the whole band, not the painted column. -->
        <rect
          class="hit"
          :x="LEFT + mark.index * band"
          :y="TOP"
          :width="band"
          :height="PLOT_H"
          @pointerenter="active = mark.index"
        />
      </g>
    </svg>

    <!-- Keyboard and screen readers: the same values without hovering. -->
    <ol class="visually-hidden">
      <li
        v-for="mark in marks"
        :key="mark.bucket.key"
        tabindex="0"
        @focus="active = mark.index"
        @blur="active = null"
      >
        {{ describe(mark.bucket) }}
      </li>
    </ol>

    <div
      v-if="tooltip"
      class="chart-tooltip"
      :style="{ left: `${tooltip.left}px`, top: `${tooltip.top}px` }"
      aria-hidden="true"
    >
      <p class="tooltip-title">{{ tooltip.bucket.title }}</p>
      <p class="tooltip-total num">{{ duration(tooltip.bucket.duration) }}</p>
      <p v-if="tooltip.bucket.billable > 0" class="tooltip-line">
        <span class="line-key billable" />
        <span class="num">{{ duration(tooltip.bucket.billable) }}</span>
        {{ t('reports.chart.billableShort') }}
        <template v-if="money(tooltip.bucket.amount)"
          >, <span class="num">{{ money(tooltip.bucket.amount) }}</span></template
        >
      </p>
    </div>
  </figure>
</template>

<style scoped>
.day-chart {
  position: relative;
  margin: 0;
}

.legend {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px 16px;
  margin-bottom: 8px;
  color: var(--text-muted);
  font-size: var(--text-xs);
}

.legend-title {
  margin-right: auto;
}

.legend-key {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.swatch {
  width: 10px;
  height: 10px;
  border-radius: 2px;
}

.swatch.billable,
.line-key.billable {
  background: var(--accent);
}

.swatch.rest {
  background: var(--chart-quiet);
}

svg {
  display: block;
  overflow: visible;
}

.grid line {
  stroke: var(--border);
  stroke-width: 1;
  shape-rendering: crispEdges;
}

.tick {
  fill: var(--text-muted);
  font-size: 11px;
}

.bar.billable {
  fill: var(--accent);
}

.bar.rest {
  fill: var(--chart-quiet);
}

[data-active] .bar {
  filter: brightness(1.12);
}

.hit {
  fill: transparent;
}

.chart-tooltip {
  position: absolute;
  z-index: 2;
  min-width: 140px;
  padding: 8px 10px;
  border-radius: var(--radius);
  background: var(--surface);
  box-shadow: var(--shadow-float);
  transform: translate(-50%, calc(-100% - 8px));
  pointer-events: none;
}

.tooltip-title {
  color: var(--text-muted);
  font-size: var(--text-xs);
}

.tooltip-total {
  font-size: var(--text-md);
  font-weight: 600;
}

.tooltip-line {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text-muted);
  font-size: var(--text-xs);
  white-space: nowrap;
}

.line-key {
  width: 10px;
  height: 2px;
  border-radius: 1px;
}

@media (prefers-reduced-motion: no-preference) {
  .bar {
    transition: filter var(--dur) var(--ease);
  }
}
</style>
