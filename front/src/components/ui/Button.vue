<template>
  <button
    class="h-10 rounded-lg uppercase flex items-center justify-center
    disabled:cursor-default px-4 min-w-[100px] transition-all"
    :class="`${currentBgAndBorder} ${block ? 'w-full' : ''} ${loading ? 'cursor-default' : 'cursor-pointer'}`"
    :type="type"
    :disabled="disabled"
    v-on:click="clickOnBtn($event)"
  >
    <Loader type="dots" v-if="loading" class="absolute" />
    <div :class="{'opacity-0': loading}">
      <slot />
    </div>
  </button>
</template>

<script setup>
import { computed } from 'vue';
import Loader from './Loader.vue';

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
    default: "button",
  },
  loading: {
    type: Boolean,
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(["click"])

function clickOnBtn(event) {
  if (!props.loading && !props.disabled) {
    emit("click", event)
  }
}

const currentBgAndBorder = computed(() => {
  if (props.outlined) {
    if (props.second) {
      // return "border border-secondary text-secondary hover:border-secondary-hover hover:text-secondary-hover"
      return "border border-secondary text-secondary hover:border-secondary-highlight hover:text-secondary-highlight"
    }
    else {
      // return "border border-primary text-primary hover:border-primary-hover hover:text-primary-hover"
      return "border border-primary text-primary hover:border-primary-highlight hover:text-primary-highlight"
    }
  }
  else {
    if (props.second) {
      // return "bg-secondary text-inverted-text hover:bg-secondary-hover"
      return "bg-secondary text-bg hover:bg-secondary-highlight"
    }
    else {
      // return "bg-primary text-primary-text hover:bg-primary-hover"
      return "bg-primary text-bg hover:bg-primary-highlight"
    }
  }
})
</script>
