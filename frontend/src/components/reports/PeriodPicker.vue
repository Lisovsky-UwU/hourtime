<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import AppIcon from '@/components/AppIcon.vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiIconButton from '@/components/ui/UiIconButton.vue'
import UiPopover from '@/components/ui/UiPopover.vue'
import { usePreferencesStore } from '@/stores/preferences'
import type { Period, PresetKey } from '@/utils/period'
import {
  PRESETS,
  formatPeriod,
  matchPreset,
  presetPeriod,
  shiftPeriod,
  weekOf,
} from '@/utils/period'

/**
 * The report period: arrows step to the previous or next period of the same
 * kind, the button opens presets as plain rows and a custom range under a
 * rule. `null` is all time.
 */
const model = defineModel<Period | null>({ required: true })

const props = withDefaults(
  defineProps<{
    /** Offers "All time" (summary and detailed). */
    allowAll?: boolean
    /** Whole weeks only: the weekly report. */
    weeks?: boolean
  }>(),
  { allowAll: false, weeks: false },
)

const { t, locale } = useI18n()
const preferences = usePreferencesStore()

const open = ref(false)
const customFrom = ref('')
const customTo = ref('')

watch(open, (value) => {
  if (!value) return
  customFrom.value = model.value?.from ?? ''
  customTo.value = model.value?.to ?? ''
})

const presets = computed<PresetKey[]>(() => (props.weeks ? ['this-week', 'last-week'] : PRESETS))

const preset = computed(() =>
  model.value ? matchPreset(model.value, preferences.weekStart) : null,
)

const title = computed(() => {
  if (!model.value) return t('reports.period.all')
  return preset.value
    ? t(`reports.period.${preset.value}`)
    : formatPeriod(model.value, locale.value)
})

/** The dates themselves, in pencil next to a preset name. */
const range = computed(() =>
  model.value && preset.value ? formatPeriod(model.value, locale.value) : '',
)

function pick(period: Period | null) {
  model.value = period
  open.value = false
}

const customValid = computed(
  () => customFrom.value !== '' && customTo.value !== '' && customFrom.value <= customTo.value,
)

function applyCustom() {
  if (!customValid.value) return
  pick(
    props.weeks
      ? weekOf(customFrom.value, preferences.weekStart)
      : { from: customFrom.value, to: customTo.value },
  )
}

function step(direction: -1 | 1) {
  if (model.value) model.value = shiftPeriod(model.value, direction)
}
</script>

<template>
  <div class="period" role="group" :aria-label="t('reports.period.label')">
    <UiIconButton
      icon="chevron-left"
      :label="t('reports.period.previous')"
      :disabled="!model"
      @click="step(-1)"
    />

    <UiPopover v-model:open="open">
      <template #trigger>
        <button
          type="button"
          class="period-trigger"
          :aria-label="`${t('reports.period.label')}: ${title} ${range}`"
        >
          <AppIcon name="calendar" :size="16" />
          <span class="period-title">{{ title }}</span>
          <span v-if="range" class="period-range">{{ range }}</span>
        </button>
      </template>

      <div class="presets">
        <button
          v-for="key in presets"
          :key="key"
          type="button"
          class="ui-menu-item preset"
          :aria-pressed="preset === key"
          @click="pick(presetPeriod(key, preferences.weekStart))"
        >
          <span class="preset-check"
            ><AppIcon v-if="preset === key" name="check" :size="16"
          /></span>
          {{ t(`reports.period.${key}`) }}
        </button>
        <button
          v-if="allowAll"
          type="button"
          class="ui-menu-item preset"
          :aria-pressed="model === null"
          @click="pick(null)"
        >
          <span class="preset-check"
            ><AppIcon v-if="model === null" name="check" :size="16"
          /></span>
          {{ t('reports.period.all') }}
        </button>
      </div>

      <form class="custom" @submit.prevent="applyCustom">
        <p class="custom-title">
          {{ weeks ? t('reports.period.weekOf') : t('reports.period.custom') }}
        </p>
        <div class="custom-fields">
          <label class="custom-field">
            <span class="visually-hidden">{{ t('reports.period.from') }}</span>
            <input v-model="customFrom" type="date" class="custom-input num" required />
          </label>
          <template v-if="!weeks">
            <span class="muted" aria-hidden="true">-</span>
            <label class="custom-field">
              <span class="visually-hidden">{{ t('reports.period.to') }}</span>
              <input
                v-model="customTo"
                type="date"
                class="custom-input num"
                :min="customFrom"
                required
              />
            </label>
          </template>
        </div>
        <UiButton type="submit" size="sm" :disabled="weeks ? customFrom === '' : !customValid">
          {{ t('reports.period.apply') }}
        </UiButton>
      </form>
    </UiPopover>

    <UiIconButton
      icon="chevron-right"
      :label="t('reports.period.next')"
      :disabled="!model"
      @click="step(1)"
    />
  </div>
</template>

<style scoped>
.period {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  min-width: 0;
}

.period-trigger {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  height: var(--control-h);
  padding: 0 12px;
  border: 1px solid var(--control-border);
  border-radius: var(--radius);
  background: var(--surface);
  color: var(--text);
  font: inherit;
  cursor: pointer;
  transition: background-color var(--dur) var(--ease);
}

.period-trigger:hover,
.period-trigger[data-state='open'] {
  background: var(--surface-muted);
}

.period-trigger > svg {
  flex: 0 0 auto;
  color: var(--text-muted);
}

.period-title {
  font-weight: 500;
  white-space: nowrap;
}

.period-range {
  overflow: hidden;
  color: var(--text-muted);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.presets {
  display: flex;
  flex-direction: column;
  min-width: 240px;
  margin: -4px;
}

.preset {
  width: 100%;
  border: 0;
  background: none;
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.preset:hover,
.preset:focus-visible {
  background: var(--surface-muted);
  outline: none;
}

.preset-check {
  display: inline-flex;
  width: 16px;
  color: var(--accent);
}

/* The custom range sits under a rule: presets cover the usual case. */
.custom {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
  margin-top: 8px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}

.custom-title {
  color: var(--text-muted);
  font-size: var(--text-xs);
}

.custom-fields {
  display: flex;
  align-items: center;
  gap: 6px;
}

.custom-input {
  height: var(--control-h-sm);
  padding: 0 6px;
  border: 1px solid var(--control-border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text);
  font: inherit;
  font-size: var(--text-sm);
}

@media (width < 600px) {
  .period-range {
    display: none;
  }
}
</style>
