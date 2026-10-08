<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import UiDialog from '@/components/ui/UiDialog.vue'

const open = defineModel<boolean>('open', { default: false })

const { t } = useI18n()

const shortcuts = [
  { key: 'N', action: 'shortcuts.focusDescription' },
  { key: 'S', action: 'shortcuts.toggleTimer' },
  { key: '?', action: 'shortcuts.help' },
]
</script>

<template>
  <UiDialog v-model:open="open" :title="t('shortcuts.title')" :description="t('shortcuts.hint')">
    <dl class="shortcuts">
      <div v-for="item in shortcuts" :key="item.key" class="shortcut">
        <dt><kbd class="num">{{ item.key }}</kbd></dt>
        <dd>{{ t(item.action) }}</dd>
      </div>
    </dl>
  </UiDialog>
</template>

<style scoped>
.shortcuts {
  margin: 0;
}

.shortcut {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  border-top: 1px solid var(--border);
}

.shortcut:first-child {
  border-top: none;
}

dd {
  margin: 0;
}

/* A key cap: the thicker bottom edge is what makes it read as a key. */
kbd {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 26px;
  height: 26px;
  padding: 0 6px;
  border: 1px solid var(--control-border);
  border-bottom-width: 2px;
  border-radius: var(--radius-sm);
  background: var(--surface-muted);
  color: var(--text);
  /* `font` resets the numeric settings of .num, so they are repeated here. */
  font: inherit;
  font-size: var(--text-xs);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  font-variation-settings: 'SHRP' 100;
}
</style>
