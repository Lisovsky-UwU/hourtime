<template>
  <div>
    <div
      class="color-base"
      :style="model === null || model === undefined ? {} : {backgroundColor: model}"
      @click="showPopUp = !showPopUp"
      id="toggle-popup"
    >
      <svg-icon v-if="model === null || model === undefined" type="mdi" :path="mdiCancel" />
    </div>

    <div
      class="grid grid-cols-5 absolute bg-bg border border-border rounded-lg
        gap-2 p-4 mt-1"
      id="color-popup"
      v-if="showPopUp"
    >
      <div
        v-for="color in colors"
        :key="color"
        class="color-base"
        :style="{backgroundColor: color}"
        @click="selectColor(color)"
      >
        <svg-icon v-if="color.toUpperCase() === model?.toUpperCase()" type="mdi" :path="mdiCheck"/>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch, type ModelRef } from 'vue';
import SvgIcon from '@jamescoyle/vue-icon'
import { mdiCancel, mdiCheck } from '@mdi/js';

const showPopUp = ref(false)

const model: ModelRef<string | null | undefined> = defineModel({required: true})

const colors = [
  "#D92B2B",
  "#E36A00",
  "#C7AF14",
  "#C9806B",
  "#BF7000",
  "#2DA608",
  "#566614",
  "#0B83D9",
  "#082D8A",
  "#9E5BD9",
  "#06A893",
  "#465BB3",
  "#D94182",
  "#990099",
  "#525266",
]

onMounted(() => {
  if (model.value === null || model.value === undefined) {
    model.value = colors[Math.floor(Math.random() * colors.length)]
  }
})

function selectColor(color: string) {
  model.value = color
  showPopUp.value = false
}

const handleClickOutside = (event: PointerEvent) => {
  const togglePopup = document.getElementById("toggle-popup")
  if (event.target === togglePopup) {
    return
  }

  const colorPopup = document.getElementById("color-popup")
  if (!colorPopup?.contains(event.target) && event.target !== colorPopup) {
    showPopUp.value = false
  }
}

watch(
  () => showPopUp.value,
  (newVal) => {
    if (newVal) {
      document.addEventListener('click', handleClickOutside)
    } else {
      document.removeEventListener('click', handleClickOutside)
    }
  }
)
</script>

<style scoped>
@import 'tailwindcss';
@import '@/assets/theme.css';

.color-base {
  @apply w-[30px] h-[30px] rounded-full hover:scale-[110%] transition-all duration-150
  cursor-pointer flex items-center justify-center;
}

.color-base.selected {
  @apply outline-[3px] outline-border outline-offset-1;
}
</style>
