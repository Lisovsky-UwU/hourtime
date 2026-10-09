<script setup lang="ts">
/**
 * The "interval" mark: an H built from [ ] brackets, the crossbar is a time
 * entry and the red dot is the running timer. Kept in sync with
 * public/favicon.svg and docs/logo*.svg.
 */
withDefaults(defineProps<{ size?: 'md' | 'lg' }>(), { size: 'md' })
</script>

<template>
  <svg class="brand-mark" :data-size="size" viewBox="0 0 32 32" aria-hidden="true">
    <path class="brackets" d="M11 6.5H6v19h5M21 6.5h5v19h-5" />
    <path class="entry" d="M11 16h6.5" />
    <circle class="live" cx="21.6" cy="16" r="2.5" />
  </svg>
</template>

<style scoped>
.brand-mark {
  flex: 0 0 auto;
  width: 28px;
  height: 28px;
  fill: none;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.brand-mark[data-size='lg'] {
  width: 40px;
  height: 40px;
}

.brackets {
  stroke: var(--text);
  stroke-width: 3;
}

.entry {
  stroke: var(--accent);
  stroke-width: 3.4;
}

.live {
  fill: var(--live);
}
</style>
