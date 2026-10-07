<script setup lang="ts">
/** The "H" stamp: the brand where there is no room for the name. */
withDefaults(defineProps<{ size?: 'md' | 'lg' }>(), { size: 'md' })
</script>

<template>
  <span class="brand-mark" :data-size="size" aria-hidden="true">H</span>
</template>

<style scoped>
.brand-mark {
  display: inline-grid;
  place-items: center;
  flex: 0 0 auto;
  width: 28px;
  height: 28px;
  border-radius: var(--radius);
  background: var(--accent);
  color: var(--accent-contrast);
  font-weight: 700;
  font-variation-settings: 'SHRP' 100;
}

.brand-mark[data-size='lg'] {
  width: 40px;
  height: 40px;
  font-size: var(--text-lg);
}
</style>
