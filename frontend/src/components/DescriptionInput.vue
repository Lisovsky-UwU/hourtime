<script setup lang="ts">
import { computed, onUnmounted, ref, useId } from 'vue'
import { useI18n } from 'vue-i18n'

import * as entriesApi from '@/api/timeEntries'
import AutoTextarea from '@/components/AutoTextarea.vue'
import { useProjectsStore } from '@/stores/projects'
import type { TimeEntrySuggestion } from '@/types'

/**
 * The timer's description with what was tracked before offered below it.
 *
 * The list opens as you type, without a highlight, so Enter keeps committing
 * the typed text until an arrow key picks a row. Arrow Down on a closed list
 * opens it on the first row. Picking hands the whole pair to the parent: the
 * project comes along.
 */
const model = defineModel<string>({ required: true })
defineProps<{ placeholder: string; label: string }>()
const emit = defineEmits<{ commit: []; pick: [TimeEntrySuggestion] }>()

const DEBOUNCE_MS = 150

const { t } = useI18n()
const projects = useProjectsStore()
const listId = useId()

const field = ref<InstanceType<typeof AutoTextarea> | null>(null)
const items = ref<TimeEntrySuggestion[]>([])
const open = ref(false)
const active = ref(-1)

let debounce: number | null = null
/** Answers can arrive out of order; only the newest request may fill the list. */
let requestSeq = 0

function close() {
  open.value = false
  active.value = -1
}

/** `byArrow`: opened from the keyboard, so it opens even for an empty field
 *  and starts on the first row. */
async function fetchFor(text: string, byArrow = false) {
  const seq = ++requestSeq
  try {
    const found = await entriesApi.suggestions(text.trim())
    if (seq !== requestSeq) return
    items.value = found
    active.value = byArrow && found.length > 0 ? 0 : -1
    open.value = found.length > 0 && (byArrow || text.trim() !== '')
  } catch {
    // Suggestions are a convenience; typing goes on without them.
    if (seq === requestSeq) close()
  }
}

function cancelPending() {
  if (debounce !== null) window.clearTimeout(debounce)
  debounce = null
}

function onInput() {
  cancelPending()
  if (!model.value.trim()) {
    requestSeq++
    close()
    return
  }
  debounce = window.setTimeout(() => {
    debounce = null
    void fetchFor(model.value)
  }, DEBOUNCE_MS)
}

function pick(item: TimeEntrySuggestion) {
  close()
  emit('pick', item)
}

function move(step: number) {
  const count = items.value.length
  active.value = active.value < 0 && step < 0 ? count - 1 : (active.value + step + count) % count
}

// Capture phase: runs before the textarea's own Enter-to-commit.
function onKeydown(event: KeyboardEvent) {
  if (event.key === 'ArrowDown' && !open.value) {
    event.preventDefault()
    // A typed-ahead request still waiting would land later and drop the highlight.
    cancelPending()
    void fetchFor(model.value, true)
    return
  }
  if (!open.value) return

  if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
    event.preventDefault()
    move(event.key === 'ArrowDown' ? 1 : -1)
  } else if (event.key === 'Enter' && !event.shiftKey && active.value >= 0) {
    event.preventDefault()
    const item = items.value[active.value]
    if (item) pick(item)
  } else if (event.key === 'Escape') {
    event.preventDefault()
    close()
  } else if (event.key === 'Tab') {
    close()
  }
}

function onBlur() {
  close()
  emit('commit')
}

const activeId = computed(() => (open.value && active.value >= 0 ? `${listId}-${active.value}` : undefined))

onUnmounted(cancelPending)

defineExpose({ focus: () => field.value?.focus() })
</script>

<template>
  <div class="description-input" @keydown.capture="onKeydown">
    <AutoTextarea
      ref="field"
      v-model="model"
      role="combobox"
      aria-autocomplete="list"
      :aria-expanded="open"
      :aria-controls="listId"
      :aria-activedescendant="activeId"
      :placeholder="placeholder"
      :aria-label="label"
      @input="onInput"
      @blur="onBlur"
    />

    <div
      v-show="open"
      :id="listId"
      class="ui-floating suggestions"
      role="listbox"
      :aria-label="t('timer.suggestions')"
      :data-state="open ? 'open' : 'closed'"
    >
      <div
        v-for="(item, index) in items"
        :id="`${listId}-${index}`"
        :key="`${item.description}\u0000${item.project_id}`"
        class="ui-menu-item suggestion"
        role="option"
        :aria-selected="index === active"
        :data-highlighted="index === active ? '' : undefined"
        @mousedown.prevent
        @mousemove="active = index"
        @click="pick(item)"
      >
        <span class="text">{{ item.description }}</span>
        <span v-if="projects.find(item.project_id)" class="project">
          <span
            class="ui-combobox-dot"
            :style="{ background: projects.find(item.project_id)?.color }"
          />
          <span class="text">{{ projects.find(item.project_id)?.name }}</span>
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.description-input {
  position: relative;
}

.suggestions {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  width: max(100%, 320px);
  max-width: calc(100vw - 32px);
  max-height: 320px;
}

.suggestion {
  justify-content: space-between;
  gap: 16px;
}

.text {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.project {
  display: inline-flex;
  align-items: center;
  flex: 0 1 auto;
  gap: 6px;
  min-width: 0;
  max-width: 45%;
  color: var(--text-muted);
  font-size: var(--text-xs);
}

.project > .ui-combobox-dot {
  flex: 0 0 auto;
}
</style>
