<script setup lang="ts">
import {
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuPortal,
  DropdownMenuRoot,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from 'reka-ui'

import AppIcon from '@/components/AppIcon.vue'
import type { IconName } from '@/components/AppIcon.vue'
import UiIconButton from '@/components/ui/UiIconButton.vue'

export type MenuEntry =
  | {
      label: string
      select: () => void
      icon?: IconName
      variant?: 'danger'
      disabled?: boolean
    }
  | 'separator'

withDefaults(
  defineProps<{
    items: MenuEntry[]
    /** Accessible name of the default "more" trigger. */
    label: string
    align?: 'start' | 'center' | 'end'
  }>(),
  { align: 'end' },
)
</script>

<template>
  <DropdownMenuRoot>
    <DropdownMenuTrigger as-child>
      <slot name="trigger">
        <UiIconButton icon="more" :label="label" :tooltip="false" />
      </slot>
    </DropdownMenuTrigger>
    <DropdownMenuPortal>
      <DropdownMenuContent class="ui-floating" :align="align" :side-offset="6" :collision-padding="8">
        <template v-for="(item, index) in items" :key="index">
          <DropdownMenuSeparator v-if="item === 'separator'" class="ui-menu-separator" />
          <DropdownMenuItem
            v-else
            class="ui-menu-item"
            :data-variant="item.variant"
            :disabled="item.disabled"
            @select="item.select"
          >
            <AppIcon v-if="item.icon" :name="item.icon" :size="16" />
            {{ item.label }}
          </DropdownMenuItem>
        </template>
      </DropdownMenuContent>
    </DropdownMenuPortal>
  </DropdownMenuRoot>
</template>
