<template>
  <button
    class="h-10 rounded-lg cursor-pointer"
    :class="`${currentBgAndBorder} ${block ? 'w-full' : ''}`"
    :type="type"
    @click="$emit('click')"
  >
    <slot/>
  </button>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  outlined: {
    type: Boolean,
    default: false,
  },
  second: {
    type: Boolean,
    default: false,
  },
  block: {
    type: Boolean,
    default: false,
  },
  type: {
    type: String,
    default: "button"
  }
})

const currentBgAndBorder = computed(() => {
  if (props.outlined) {
    if (props.second) {
      return "border border-secondary text-secondary"
    }
    else {
      return "border border-primary text-primary"
    }
  }
  else {
    if (props.second) {
      return "bg-secondary text-inverted"
    }
    else {
      return "bg-primary text-primary-text"
    }
  }
})
</script>
