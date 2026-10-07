<script setup lang="ts">
import { PopoverContent, PopoverPortal, PopoverRoot, PopoverTrigger } from 'reka-ui'

const open = defineModel<boolean>('open', { default: false })

withDefaults(
  defineProps<{
    side?: 'top' | 'right' | 'bottom' | 'left'
    align?: 'start' | 'center' | 'end'
  }>(),
  { side: 'bottom', align: 'start' },
)
</script>

<template>
  <PopoverRoot v-model:open="open">
    <PopoverTrigger as-child>
      <slot name="trigger" />
    </PopoverTrigger>
    <PopoverPortal>
      <PopoverContent
        class="ui-floating ui-popover"
        :side="side"
        :align="align"
        :side-offset="6"
        :collision-padding="8"
      >
        <slot :close="() => (open = false)" />
      </PopoverContent>
    </PopoverPortal>
  </PopoverRoot>
</template>

<style>
/* Doubled class: wins over .ui-floating whatever order the stylesheets load in. */
.ui-floating.ui-popover {
  padding: 12px;
  max-width: min(360px, calc(100vw - 16px));
}
</style>
