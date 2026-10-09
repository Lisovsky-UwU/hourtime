<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  ColorAreaArea,
  ColorAreaRoot,
  ColorAreaThumb,
  ColorFieldInput,
  ColorFieldRoot,
  ColorSliderRoot,
  ColorSliderThumb,
  ColorSliderTrack,
  ColorSwatchPickerItem,
  ColorSwatchPickerItemSwatch,
  ColorSwatchPickerRoot,
} from 'reka-ui'

import UiPopover from '@/components/ui/UiPopover.vue'
import { PROJECT_COLORS } from '@/utils/projectColors'

/**
 * The ready-made palette plus a picker for anything else. The palette is one
 * listbox: Tab enters it once, arrows move between colors.
 */
const model = defineModel<string>({ required: true })
const { t } = useI18n()

const normalized = computed(() => model.value.toLowerCase())
const isPreset = computed(() => PROJECT_COLORS.some((color) => color.value === normalized.value))

function pickPreset(value: unknown) {
  if (typeof value === 'string') model.value = value
}
</script>

<template>
  <div class="color-picker">
    <ColorSwatchPickerRoot
      :model-value="isPreset ? normalized : undefined"
      class="swatches"
      orientation="horizontal"
      :aria-label="t('projects.form.preset')"
      @update:model-value="pickPreset"
    >
      <ColorSwatchPickerItem
        v-for="color in PROJECT_COLORS"
        :key="color.value"
        :value="color.value"
        class="swatch"
        :aria-label="t(`projects.colors.${color.name}`)"
      >
        <ColorSwatchPickerItemSwatch class="swatch-face" />
      </ColorSwatchPickerItem>
    </ColorSwatchPickerRoot>

    <UiPopover>
      <template #trigger>
        <button type="button" class="custom">
          <span
            class="swatch"
            :data-state="isPreset ? undefined : 'checked'"
            :style="{ background: model }"
          />
          <span>{{ t('projects.form.customColor') }}</span>
          <span class="num muted">{{ normalized }}</span>
        </button>
      </template>

      <div class="custom-panel">
        <ColorAreaRoot
          v-slot="{ style }"
          v-model="model"
          color-space="hsb"
          x-channel="saturation"
          y-channel="brightness"
        >
          <ColorAreaArea class="area" :style="style">
            <ColorAreaThumb class="thumb" />
          </ColorAreaArea>
        </ColorAreaRoot>

        <ColorSliderRoot
          v-model="model"
          color-space="hsb"
          channel="hue"
          class="hue"
        >
          <ColorSliderTrack class="hue-track" />
          <ColorSliderThumb class="thumb" />
        </ColorSliderRoot>

        <ColorFieldRoot v-model="model" class="hex">
          <ColorFieldInput class="hex-input num" :aria-label="t('projects.form.customColor')" />
        </ColorFieldRoot>
      </div>
    </UiPopover>
  </div>
</template>

<style scoped>
.color-picker {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* The listbox root renders more than one node, so it does not get this
   component's scope attribute. */
.color-picker :deep(.swatches) {
  display: grid;
  grid-template-columns: repeat(6, 28px);
  gap: 8px;
  outline: none;
}

.swatch {
  position: relative;
  display: block;
  flex: 0 0 auto;
  width: 28px;
  height: 28px;
  padding: 0;
  border: 0;
  border-radius: 50%;
  cursor: pointer;
  outline: none;
}

.swatch-face {
  display: block;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: var(--reka-color-swatch-color);
}

/* The ring sits outside the dot, so the chosen color itself stays visible. */
.swatch[data-state='checked']::after {
  content: '';
  position: absolute;
  inset: -4px;
  border: 2px solid var(--text);
  border-radius: 50%;
}

/* Arrow keys move the highlight; it shows only for the keyboard. */
.color-picker :deep(.swatches:focus-within) .swatch[data-highlighted] {
  outline: 2px solid var(--focus);
  outline-offset: 6px;
}

.custom {
  display: flex;
  align-items: center;
  gap: 10px;
  align-self: flex-start;
  padding: 0;
  border: 0;
  background: none;
  color: var(--text);
  font: inherit;
  cursor: pointer;
}

.custom:focus-visible {
  outline: 2px solid var(--focus);
  outline-offset: 4px;
  border-radius: var(--radius-sm);
}

.custom-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 220px;
}

.area {
  position: relative;
  height: 140px;
  border-radius: var(--radius-sm);
}

.hue {
  position: relative;
  display: flex;
  align-items: center;
  height: 14px;
  touch-action: none;
}

.hue-track {
  position: relative;
  flex: 1;
  height: 10px;
  border-radius: var(--radius-full);
}

.thumb {
  display: block;
  width: 14px;
  height: 14px;
  border: 2px solid #fff;
  border-radius: 50%;
  box-shadow: 0 0 0 1px rgb(0 0 0 / 0.35);
  cursor: grab;
  outline: none;
}

.thumb:focus-visible {
  box-shadow: 0 0 0 2px var(--focus);
}

.hex-input {
  width: 100%;
  height: var(--control-h-sm);
  padding: 0 8px;
  border: 1px solid var(--control-border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text);
  font: inherit;
  font-size: var(--text-sm);
}

.hex-input:focus-visible {
  outline: 2px solid var(--focus);
  outline-offset: -1px;
}
</style>
