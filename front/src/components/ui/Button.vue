<template>
  <button
    class="h-10 rounded-lg uppercase flex items-center justify-center
    disabled:cursor-default px-4 min-w-[100px] transition-all"
    :class="`${currentBgAndBorder()} ${block ? 'w-full' : ''} ${loading ? 'cursor-default' : 'cursor-pointer'}`"
    :type="type"
    :disabled="disabled"
    v-on:click="clickOnBtn($event)"
  >
    <Loader type="dots" v-if="loading" class="absolute" />
    <div :class="{'opacity-0': loading}" class="flex flex-row gap-3">
      <slot />
    </div>
  </button>
</template>

<script setup lang="ts">
import { type PropType } from 'vue';
import Loader from './Loader.vue';

enum Color {
  LIGHT = "light",
  DARK = "dark",
  PRIMARY = "primary",
  SECOND = "second",
  DANGER = "danger",
}

const props = defineProps({
  color: {
    type: String as PropType<Color>,
    default: "light"
  },
  outlined: {
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

// const currentBgAndBorder = computed(() => {
function currentBgAndBorder() {
  let base, hover, text;
  switch (props.color) {
    case Color.LIGHT:
      base = "bg-light"
      text = "text"
      hover = "bg-dark"
      break;
    case Color.DARK:
      base = "bg-dark"
      text = "text"
      hover = "bg-light"
      break;
    case Color.PRIMARY:
      base = "primary"
      text = "bg"
      hover = "primary-highlight"
      break;
    case Color.SECOND:
      base = "secondary"
      text = "bg"
      hover = "secondary-highlight"
      break;
    case Color.DANGER:
      base = "danger"
      text = "text"
      hover = "danger-highlight"
      break;
    default:
      base = "bg-light"
      text = "text"
      hover = "bg-dark"
      break;
  }

  if (props.outlined) {
    return `border border-${base} text-${base} hover:border-${hover} hover:text-${hover}`
  } else {
    return `bg-${base} text-${text} hover:bg-${hover}`
  }
// })
}
</script>

<style scoped>
@import 'tailwindcss';
@import '@/assets/theme.css';

</style>
