<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import { useAuthStore } from '@/stores/auth'
import { useEntriesStore } from '@/stores/entries'
import { useProjectsStore } from '@/stores/projects'
import { useTimerStore } from '@/stores/timer'

const { t } = useI18n()
const auth = useAuthStore()
const timer = useTimerStore()
const projects = useProjectsStore()
const entries = useEntriesStore()
const router = useRouter()

const showChrome = computed(() => auth.isAuthenticated)

async function signOut() {
  await auth.signOut()
  timer.reset()
  projects.reset()
  entries.reset()
  await router.push({ name: 'login' })
}
</script>

<template>
  <header v-if="showChrome" class="topbar">
    <div class="topbar-inner">
      <RouterLink :to="{ name: 'timer' }" class="brand">{{ t('app.name') }}</RouterLink>

      <nav class="nav">
        <RouterLink :to="{ name: 'timer' }">{{ t('nav.timer') }}</RouterLink>
        <RouterLink :to="{ name: 'projects' }">{{ t('nav.projects') }}</RouterLink>
        <RouterLink :to="{ name: 'settings' }">{{ t('nav.settings') }}</RouterLink>
      </nav>

      <span class="spacer" />

      <span class="muted small hide-narrow">{{ auth.user?.email }}</span>
      <button type="button" class="btn-ghost" @click="signOut">{{ t('nav.signOut') }}</button>
    </div>
  </header>

  <main>
    <RouterView />
  </main>
</template>

<style scoped>
.topbar {
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 10;
}

.topbar-inner {
  max-width: 900px;
  margin: 0 auto;
  padding: 10px 16px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.brand {
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.01em;
}

.brand:hover {
  text-decoration: none;
}

.nav {
  display: flex;
  gap: 4px;
}

.nav a {
  padding: 6px 10px;
  border-radius: var(--radius-sm);
  color: var(--text-muted);
}

.nav a:hover {
  background: var(--surface-muted);
  text-decoration: none;
}

.nav a.router-link-active {
  color: var(--text);
  background: var(--surface-muted);
  font-weight: 500;
}

@media (width <= 560px) {
  .hide-narrow {
    display: none;
  }
}
</style>
