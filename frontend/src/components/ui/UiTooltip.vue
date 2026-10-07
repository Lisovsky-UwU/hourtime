<script setup lang="ts">
import { TooltipContent, TooltipPortal, TooltipRoot, TooltipTrigger } from 'reka-ui'

/**
 * Wraps a single focusable element. An empty `content` renders the element
 * alone, so wrappers can switch the tooltip off without duplicating markup.
 * Needs the TooltipProvider mounted in App.vue.
 */
withDefaults(defineProps<{ content: string; side?: 'top' | 'right' | 'bottom' | 'left' }>(), {
  side: 'top',
})
</script>

<template>
  <slot v-if="!content" />
  <TooltipRoot v-else>
    <TooltipTrigger as-child>
      <slot />
    </TooltipTrigger>
    <TooltipPortal>
      <TooltipContent class="ui-tooltip" :side="side" :side-offset="6" :collision-padding="8">
        {{ content }}
      </TooltipContent>
    </TooltipPortal>
  </TooltipRoot>
</template>

