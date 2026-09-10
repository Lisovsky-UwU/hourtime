<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

/** A palette of ready-made colours plus a native picker for anything else. */
const PRESETS = [
  '#4285f4',
  '#2f6df6',
  '#0b8043',
  '#1f9d55',
  '#8bc34a',
  '#c0ca33',
  '#f4b400',
  '#f57c00',
  '#e8710a',
  '#db4437',
  '#c2185b',
  '#e91e63',
  '#9c27b0',
  '#673ab7',
  '#3f51b5',
  '#00acc1',
  '#0097a7',
  '#00897b',
  '#795548',
  '#607d8b',
  '#455a64',
  '#9e9e9e',
  '#546e7a',
  '#212121',
]

const model = defineModel<string>({ required: true })
const { t } = useI18n()

const isCustom = computed(() => !PRESETS.includes(model.value.toLowerCase()))

function pick(color: string) {
  model.value = color
}
</script>

<template>
  <div class="stack" style="gap: 10px">
    <div>
      <label>{{ t('projects.form.preset') }}</label>
      <div class="swatches">
        <button
          v-for="color in PRESETS"
          :key="color"
          type="button"
          class="swatch"
          :class="{ selected: color === model.toLowerCase() }"
          :style="{ background: color }"
          :aria-label="color"
          :aria-pressed="color === model.toLowerCase()"
          @click="pick(color)"
        />
      </div>
    </div>

    <div class="row">
      <label class="custom-label" for="custom-color">{{ t('projects.form.customColor') }}</label>
      <input id="custom-color" v-model="model" type="color" class="custom-input" />
      <span class="mono small muted">{{ model }}</span>
      <span v-if="isCustom" class="badge">{{ t('projects.form.customColor') }}</span>
    </div>
  </div>
</template>

<style scoped>
.swatches {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(28px, 1fr));
  gap: 6px;
}

.swatch {
  aspect-ratio: 1;
  padding: 0;
  border-radius: 50%;
  border: 2px solid transparent;
  box-shadow: inset 0 0 0 1px rgb(0 0 0 / 12%);
}

.swatch:hover {
  transform: scale(1.08);
}

.swatch.selected {
  border-color: var(--text);
}

.custom-label {
  margin: 0;
  white-space: nowrap;
}

.custom-input {
  width: 44px;
  height: 32px;
  padding: 2px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
}
</style>
