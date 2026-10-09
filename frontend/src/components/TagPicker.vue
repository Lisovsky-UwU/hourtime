<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  ListboxContent,
  ListboxFilter,
  ListboxItem,
  ListboxItemIndicator,
  ListboxRoot,
  PopoverContent,
  PopoverPortal,
  PopoverRoot,
  PopoverTrigger,
} from 'reka-ui'

import AppIcon from '@/components/AppIcon.vue'
import { toast } from '@/components/ui/toast'
import { messageFor } from '@/composables/useApiError'
import { useTagsStore } from '@/stores/tags'

/**
 * Tags of an entry: a tag icon with the count, opening a searchable list with
 * checkboxes and "Create" for a new name.
 *
 * Ticks only change a draft; the model is updated once, when the list closes,
 * so picking three tags is one save rather than three.
 */
const model = defineModel<string[]>({ required: true })
withDefaults(defineProps<{ disabled?: boolean }>(), { disabled: false })

const { t } = useI18n()
const tags = useTagsStore()

const open = ref(false)
const query = ref('')
const draft = ref<string[]>([])

/** Ids of deleted tags are dropped here, so they neither count nor get saved back. */
const current = computed(() => model.value.filter((id) => tags.byId.has(id)))
const names = computed(() => tags.namesOf(current.value))

watch(open, (value) => {
  if (value) {
    draft.value = [...current.value]
    return
  }
  query.value = ''
  const changed =
    draft.value.length !== current.value.length ||
    draft.value.some((id) => !current.value.includes(id))
  if (changed) model.value = [...draft.value]
})

const normalizedQuery = computed(() => query.value.trim().toLocaleLowerCase())

const filtered = computed(() =>
  normalizedQuery.value
    ? tags.sorted.filter((tag) => tag.name.toLocaleLowerCase().includes(normalizedQuery.value))
    : tags.sorted,
)

const canCreate = computed(
  () =>
    normalizedQuery.value !== '' &&
    !tags.items.some((tag) => tag.name.toLocaleLowerCase() === normalizedQuery.value),
)

// Never a real id, so it cannot collide with a tag.
const CREATE = '\u0000create'
const creating = ref(false)

async function select(values: unknown) {
  const picked = Array.isArray(values) ? values.filter((v): v is string => typeof v === 'string') : []
  if (!picked.includes(CREATE)) {
    draft.value = picked
    return
  }
  if (creating.value) return
  creating.value = true
  try {
    const tag = await tags.create(query.value.trim())
    draft.value = [...draft.value, tag.id]
    query.value = ''
  } catch (cause) {
    toast.error(t('tags.createFailed'), messageFor(cause))
  } finally {
    creating.value = false
  }
}

const triggerLabel = computed(() =>
  names.value.length ? `${t('tags.label')}: ${names.value.join(', ')}` : t('tags.add'),
)
</script>

<template>
  <PopoverRoot v-model:open="open">
    <PopoverTrigger as-child>
      <button
        type="button"
        class="tag-trigger"
        :aria-label="triggerLabel"
        :title="names.join(', ') || t('tags.add')"
        :disabled="disabled"
        :data-empty="names.length ? undefined : ''"
      >
        <AppIcon name="tag" :size="16" />
        <span v-if="names.length" class="count num">{{ names.length }}</span>
      </button>
    </PopoverTrigger>

    <PopoverPortal>
      <PopoverContent
        class="ui-floating ui-combobox"
        align="end"
        :side-offset="6"
        :collision-padding="8"
      >
        <ListboxRoot
          :model-value="draft"
          multiple
          selection-behavior="toggle"
          highlight-on-hover
          @update:model-value="select"
        >
          <div class="ui-combobox-search">
            <AppIcon name="search" :size="16" />
            <ListboxFilter
              v-model="query"
              auto-focus
              class="ui-combobox-input"
              :placeholder="t('tags.search')"
              :aria-label="t('tags.search')"
            />
          </div>

          <ListboxContent class="ui-combobox-list">
            <ListboxItem
              v-for="tag in filtered"
              :key="tag.id"
              :value="tag.id"
              class="ui-menu-item"
            >
              <span class="box" aria-hidden="true">
                <ListboxItemIndicator class="box-check">
                  <AppIcon name="check" :size="14" />
                </ListboxItemIndicator>
              </span>
              <span class="ui-combobox-label">{{ tag.name }}</span>
            </ListboxItem>

            <ListboxItem v-if="canCreate" :value="CREATE" class="ui-menu-item ui-combobox-create">
              <AppIcon name="plus" :size="16" />
              <span class="ui-combobox-label">{{ t('ui.create', { name: query.trim() }) }}</span>
            </ListboxItem>

            <p v-if="!filtered.length && !canCreate" class="ui-combobox-empty">
              {{ tags.items.length ? t('ui.noResults') : t('tags.pickerEmpty') }}
            </p>
          </ListboxContent>
        </ListboxRoot>
      </PopoverContent>
    </PopoverPortal>
  </PopoverRoot>
</template>

<style scoped>
.tag-trigger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  min-width: var(--control-h-sm);
  height: var(--control-h-sm);
  padding: 0 6px;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  background: transparent;
  /* Ink when the entry has tags, pencil when it has none: the state is the color. */
  color: var(--text);
  font: inherit;
  font-size: var(--text-xs);
  font-weight: 500;
  cursor: pointer;
  transition: background-color var(--dur) var(--ease);
}

.tag-trigger[data-empty] {
  color: var(--text-muted);
}

.tag-trigger:hover:not(:disabled),
.tag-trigger[data-state='open'] {
  background: var(--surface-muted);
}

.tag-trigger:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.count {
  min-width: 1ch;
}
</style>
