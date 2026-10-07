<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'

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

// A narrower or wider column re-wraps the text: sidebar toggles, window resizes.
let observer: ResizeObserver | null = null
let lastWidth = 0

onMounted(() => {
  resize()
  observer = new ResizeObserver(([entry]) => {
    const width = entry?.contentRect.width ?? 0
    if (width === lastWidth) return
    lastWidth = width
    resize()
  })
  if (field.value) observer.observe(field.value)
})

onUnmounted(() => observer?.disconnect())
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
/* Looks like plain text until hovered or focused: the row itself is the form. */
textarea {
  display: block;
  width: 100%;
  min-height: 0;
  padding: 5px 8px;
  border: 1px solid transparent;
  border-radius: var(--radius);
  background: transparent;
  color: var(--text);
  font: inherit;
  line-height: 1.45;
  resize: none;
  overflow: hidden;
  transition:
    background-color var(--dur) var(--ease),
    border-color var(--dur) var(--ease);
}

textarea::placeholder {
  color: var(--text-muted);
  opacity: 1;
}

textarea:hover {
  border-color: var(--border);
}

textarea:focus {
  border-color: var(--border-strong);
  background: var(--surface);
}

textarea:focus-visible {
  outline: 2px solid var(--focus);
  outline-offset: -1px;
}

@media (width < 768px) {
  textarea {
    font-size: max(1em, var(--text-md));
  }
}
</style>
