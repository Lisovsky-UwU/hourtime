<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { RadioGroupItem, RadioGroupRoot } from 'reka-ui'

import { PROJECT_COLORS } from '@/utils/projectColors'

/**
 * The ready-made palette plus a native picker for anything else. The palette
 * is one radio group: Tab enters it once, arrows move between colors.
 */
const model = defineModel<string>({ required: true })
const { t } = useI18n()

const normalized = computed(() => model.value.toLowerCase())
const isPreset = computed(() => PROJECT_COLORS.some((color) => color.value === normalized.value))
</script>

<template>
  <div class="color-picker">
    <RadioGroupRoot
      :model-value="isPreset ? normalized : undefined"
      class="swatches"
      orientation="horizontal"
      loop
      :aria-label="t('projects.form.preset')"
      @update:model-value="(value) => (model = String(value))"
    >
      <RadioGroupItem
        v-for="color in PROJECT_COLORS"
        :key="color.value"
        :value="color.value"
        class="swatch"
        :style="{ background: color.value }"
        :aria-label="t(`projects.colors.${color.name}`)"
      />
    </RadioGroupRoot>

    <label class="custom">
      <span
        class="swatch custom-swatch"
        :data-state="isPreset ? undefined : 'checked'"
        :style="{ background: model }"
      >
        <input v-model="model" type="color" class="custom-input" />
      </span>
      <span>{{ t('projects.form.customColor') }}</span>
      <span class="num muted">{{ normalized }}</span>
    </label>
  </div>
</template>

<style scoped>
.color-picker {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.swatches {
  display: grid;
  grid-template-columns: repeat(6, 28px);
  gap: 8px;
}

.swatch {
  position: relative;
  width: 28px;
  height: 28px;
  padding: 0;
  border: 0;
  border-radius: 50%;
  cursor: pointer;
}

/* The ring sits outside the dot, so the chosen color itself stays visible. */
.swatch[data-state='checked']::after {
  content: '';
  position: absolute;
  inset: -4px;
  border: 2px solid var(--text);
  border-radius: 50%;
}

.custom {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
  color: var(--text);
  cursor: pointer;
}

.custom-swatch {
  display: inline-block;
  flex: 0 0 auto;
}

/* The native control stays clickable but invisible; the swatch is its face. */
.custom-input {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
}

.custom-swatch:has(.custom-input:focus-visible) {
  outline: 2px solid var(--focus);
  outline-offset: 2px;
}
</style>
