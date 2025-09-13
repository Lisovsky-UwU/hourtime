<template>
  <button
    class="h-10 rounded-lg uppercase flex items-center justify-center
    disabled:cursor-default px-4 min-w-[100px]"
    :class="`${currentBgAndBorder} ${block ? 'w-full' : ''} ${loading ? 'cursor-default' : 'cursor-pointer'}`"
    :type="type"
    :disabled="disabled"
    v-on:click="clickOnBtn($event)"
  >
    <div v-if="loading" class="loader absolute" />
    <div :class="{'opacity-0': loading}">
      <slot />
    </div>
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

<style scoped>
.loader {
  width: 4px;
  aspect-ratio: 1;
  border-radius: 50%;
  box-shadow: 19px 0 0 7px, 38px 0 0 3px, 57px 0 0 0;
  transform: translateX(-38px);
  animation: l21 .5s infinite alternate linear;
}

@keyframes l21 {
  50%  {box-shadow: 19px 0 0 3px, 38px 0 0 7px, 57px 0 0 3px}
  100% {box-shadow: 19px 0 0 0  , 38px 0 0 3px, 57px 0 0 7px}
}
</style>
