<template>
  <input
    v-model="inputValue"
    class="border border-border p-1 text-text rounded-lg text-center w-[90px]
    focus:border-highlight transition-all focus:outline-none"
    maxlength="5"
    placeholder="12:34"
    @blur="onBlur"
    @keydown="onKeydown"
  />
</template>

<script setup lang="ts">
import dayjs, { Dayjs } from 'dayjs'
import { ref, watch } from 'vue'

const model = defineModel<Dayjs>({required: false})

const inputValue = ref("")

watch(
  () => model.value,
  (newVal) => {
    inputValue.value = newVal !== undefined ? newVal.format("HH:mm") : ""
  },
  { immediate: true }
)

function applyNewValue() {
  try {
    const newTime = dayjs(inputValue.value, "H:m")
    if (!newTime.isValid()) {
      throw Error()
    }
    if (model.value?.hour() === newTime.hour() && model.value?.minute() === newTime.minute() &&
      model.value?.second() === newTime.second()) {
      return
    }
    if (model.value !== undefined) {
      model.value = model.value
        .hour(newTime.hour())
        .minute(newTime.minute())
        .second(newTime.second())
    } else {
      model.value = newTime
    }
  } catch (e) {
    inputValue.value = model.value !== undefined ? model.value.format("HH:mm") : ""
  }
}

const onBlur = () => {
  applyNewValue()
}

const onKeydown = (e: KeyboardEvent) => {
  if (e.key === "Enter") {
    applyNewValue()
    return
  }

  if (inputValue.value.includes(":") && e.key === ":") {
    e.preventDefault()
    return
  }
  if (
    e.key === 'Backspace' ||
    e.key === 'Delete' ||
    e.key === 'ArrowLeft' ||
    e.key === 'ArrowRight' ||
    e.key === 'Tab' ||
    e.key === 'Escape' ||
    e.key === ':' ||
    e.ctrlKey ||
    e.metaKey
  ) {
    return
  }

  if (!/^\d$/.test(e.key)) {
    e.preventDefault()
    return
  }
}
</script>
