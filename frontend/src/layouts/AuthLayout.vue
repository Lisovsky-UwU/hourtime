<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import BrandMark from '@/components/BrandMark.vue'

/** Sign-in and sign-up: the brand above one sheet with the form. */
const { t } = useI18n()
</script>

<template>
  <div class="auth">
    <div class="auth-column">
      <header class="auth-brand">
        <BrandMark size="lg" />
        <div>
          <p class="brand-name">{{ t('app.name') }}</p>
          <p class="tagline">{{ t('app.tagline') }}</p>
        </div>
      </header>
      <main class="auth-sheet">
        <slot />
      </main>
    </div>
  </div>
</template>

<style scoped>
.auth {
  min-height: 100dvh;
  display: grid;
  place-items: center;
  padding: 32px 16px;
}

.auth-column {
  width: min(380px, 100%);
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.auth-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-left: 4px;
}

.brand-name {
  font-size: var(--text-xl);
  font-weight: 600;
  line-height: 1.1;
  letter-spacing: -0.01em;
  font-variation-settings: 'SHRP' 100;
}

.tagline {
  color: var(--text-muted);
}

.auth-sheet {
  padding: 24px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sheet);
  background: var(--surface);
}
</style>
