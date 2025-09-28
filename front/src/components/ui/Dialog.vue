<template>
  <Teleport to="body">
    <Transition name="dialog">
      <div v-if="model" class="dialog-overlay" @mousedown="close">
        <div class="card min-w-[400px] p-4" @mousedown.stop="">
          <slot />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { onBeforeUnmount, watch } from 'vue'

const model = defineModel()

const close = () => {
  model.value = false
}

const handleKeydown = (event) => {
  if (event.key === 'Escape') {
    close()
  }
}

watch(
  () => model,
  (model) => {
    if (model) {
      document.addEventListener('keydown', handleKeydown)
    } else {
      document.removeEventListener('keydown', handleKeydown)
    }
  },
  { immediate: true }
)

onBeforeUnmount(() => {
  document.removeEventListener('keydown', handleKeydown)
})

</script>

<style scoped>
@import 'tailwindcss';
@import '@/assets/theme.css';

/* Overlay: фон с затемнением */
.dialog-overlay {
  @apply fixed top-0 left-0 w-screen h-screen flex justify-center items-center z-50 bg-bg-overlay;
}

.dialog-enter-from {
  opacity: 0;
}
.dialog-enter-from .dialog {
  transform: translateY(-20px);
  opacity: 0;
}

.dialog-enter-to {
  opacity: 1;
}
.dialog-enter-to .dialog {
  transform: translateY(0);
  opacity: 1;
}

.dialog-leave-from {
  opacity: 1;
}
.dialog-leave-from .dialog {
  transform: translateY(0);
  opacity: 1;
}

.dialog-leave-to {
  opacity: 0;
}
.dialog-leave-to .dialog {
  transform: translateY(-20px);
  opacity: 0;
}

.dialog-enter-active,
.dialog-leave-active {
  @apply transition-all;
}
</style>
