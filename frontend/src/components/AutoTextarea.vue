<script setup lang="ts">
import { nextTick, onMounted, ref, watch } from 'vue'

/**
 * A comment box that is one line tall until the comment needs more.
 *
 * Enter commits (blur) instead of inserting a newline; Shift+Enter adds the
 * line break, which is the convention people already expect from chat inputs.
 */
const model = defineModel<string>({ required: true })
const field = ref<HTMLTextAreaElement | null>(null)

function resize() {
  const node = field.value
  if (!node) return
  // Collapse first: scrollHeight only shrinks if the box is not already tall.
  node.style.height = 'auto'
  node.style.height = `${node.scrollHeight}px`
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    field.value?.blur()
  }
}

watch(model, () => void nextTick(resize))
onMounted(resize)
</script>

<template>
  <textarea
    ref="field"
    v-model="model"
    rows="1"
    spellcheck="false"
    @input="resize"
    @keydown="onKeydown"
  />
</template>

<style scoped>
textarea {
  display: block;
  width: 100%;
  resize: none;
  overflow: hidden;
  min-height: 0;
  line-height: 1.45;
}
</style>
