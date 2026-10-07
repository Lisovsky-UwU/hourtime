<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  DialogContent,
  DialogDescription,
  DialogOverlay,
  DialogPortal,
  DialogRoot,
  DialogTitle,
} from 'reka-ui'

import AppIcon from '@/components/AppIcon.vue'
import BrandMark from '@/components/BrandMark.vue'
import type { IconName } from '@/components/AppIcon.vue'
import RunningIndicator from '@/components/RunningIndicator.vue'
import UiIconButton from '@/components/ui/UiIconButton.vue'
import UiTooltip from '@/components/ui/UiTooltip.vue'
import { useAuthStore } from '@/stores/auth'
import { useEntriesStore } from '@/stores/entries'
import { usePreferencesStore } from '@/stores/preferences'
import { useProjectsStore } from '@/stores/projects'
import { useTimerStore } from '@/stores/timer'

/**
 * Signed-in chrome: a sidebar on wide screens, a top bar with a slide-out
 * menu on phones. Every stage of the plan adds its own item here; sections
 * that do not exist yet are not listed.
 */
const { t } = useI18n()
const auth = useAuthStore()
const timer = useTimerStore()
const projects = useProjectsStore()
const entries = useEntriesStore()
const preferences = usePreferencesStore()
const router = useRouter()
const route = useRoute()

interface NavItem {
  name: string
  icon: IconName
  label: string
}

const main: NavItem[] = [
  { name: 'timer', icon: 'timer', label: 'nav.timer' },
  { name: 'projects', icon: 'projects', label: 'nav.projects' },
]
const secondary: NavItem[] = [{ name: 'settings', icon: 'settings', label: 'nav.settings' }]

const drawerOpen = ref(false)
watch(
  () => route.fullPath,
  () => (drawerOpen.value = false),
)

// The indicator lives in the chrome, so the timer has to be known on every
// screen, not only after the timer page has been opened.
void timer.sync().catch(() => {})
void projects.load().catch(() => {})

/**
 * Keeps the indicator honest on screens other than the timer, which runs its
 * own, fuller resync. `focus` and `visibilitychange` arrive together, hence
 * the short collapse window.
 */
let pendingSync: number | null = null

function resyncTimer() {
  if (route.name === 'timer' || document.visibilityState !== 'visible') return
  if (pendingSync !== null) return
  pendingSync = window.setTimeout(() => {
    pendingSync = null
    void timer.sync().catch(() => {})
  }, 100)
}

onMounted(() => {
  document.addEventListener('visibilitychange', resyncTimer)
  window.addEventListener('focus', resyncTimer)
})

onUnmounted(() => {
  if (pendingSync !== null) window.clearTimeout(pendingSync)
  document.removeEventListener('visibilitychange', resyncTimer)
  window.removeEventListener('focus', resyncTimer)
})

async function signOut() {
  await auth.signOut()
  timer.reset()
  projects.reset()
  entries.reset()
  await router.push({ name: 'login' })
}
</script>

<template>
  <div class="shell" :data-collapsed="preferences.sidebarCollapsed ? '' : undefined">
    <a class="skip-link" href="#content">{{ t('nav.skipToContent') }}</a>

    <aside class="sidebar">
      <div class="brand-row">
        <RouterLink :to="{ name: 'timer' }" class="brand" :aria-label="t('app.name')">
          <BrandMark />
          <span class="brand-name">{{ t('app.name') }}</span>
        </RouterLink>
        <UiIconButton
          icon="sidebar"
          :aria-expanded="!preferences.sidebarCollapsed"
          size="sm"
          :label="preferences.sidebarCollapsed ? t('nav.expand') : t('nav.collapse')"
          @click="preferences.sidebarCollapsed = !preferences.sidebarCollapsed"
        />
      </div>

      <RunningIndicator class="sidebar-running" :compact="preferences.sidebarCollapsed" />

      <nav class="nav" :aria-label="t('nav.main')">
        <UiTooltip
          v-for="item in main"
          :key="item.name"
          :content="preferences.sidebarCollapsed ? t(item.label) : ''"
          side="right"
        >
          <RouterLink :to="{ name: item.name }" class="nav-link">
            <AppIcon :name="item.icon" />
            <span class="nav-label">{{ t(item.label) }}</span>
          </RouterLink>
        </UiTooltip>
      </nav>

      <div class="sidebar-foot">
        <UiTooltip
          v-for="item in secondary"
          :key="item.name"
          :content="preferences.sidebarCollapsed ? t(item.label) : ''"
          side="right"
        >
          <RouterLink :to="{ name: item.name }" class="nav-link">
            <AppIcon :name="item.icon" />
            <span class="nav-label">{{ t(item.label) }}</span>
          </RouterLink>
        </UiTooltip>

        <div class="account">
          <span class="email" :title="auth.user?.email">{{ auth.user?.email }}</span>
          <UiIconButton icon="sign-out" size="sm" :label="t('nav.signOut')" @click="signOut" />
        </div>
      </div>
    </aside>

    <header class="topbar">
      <UiIconButton icon="menu" :label="t('nav.openMenu')" @click="drawerOpen = true" />
      <RouterLink :to="{ name: 'timer' }" class="brand">
        <span class="brand-name">{{ t('app.name') }}</span>
      </RouterLink>
      <span class="spacer" />
      <RunningIndicator compact />
    </header>

    <DialogRoot v-model:open="drawerOpen">
      <DialogPortal>
        <DialogOverlay class="drawer-overlay" />
        <DialogContent class="drawer">
          <div class="drawer-head">
            <DialogTitle class="brand-name">{{ t('app.name') }}</DialogTitle>
            <DialogDescription class="visually-hidden">{{ t('nav.main') }}</DialogDescription>
            <UiIconButton icon="close" :label="t('common.close')" @click="drawerOpen = false" />
          </div>
          <RunningIndicator />
          <nav class="nav" :aria-label="t('nav.main')">
            <RouterLink
              v-for="item in [...main, ...secondary]"
              :key="item.name"
              :to="{ name: item.name }"
              class="nav-link"
            >
              <AppIcon :name="item.icon" />
              <span class="nav-label">{{ t(item.label) }}</span>
            </RouterLink>
          </nav>
          <div class="account drawer-account">
            <span class="email">{{ auth.user?.email }}</span>
            <UiIconButton icon="sign-out" :label="t('nav.signOut')" @click="signOut" />
          </div>
        </DialogContent>
      </DialogPortal>
    </DialogRoot>

    <main id="content" class="content" tabindex="-1">
      <slot />
    </main>
  </div>
</template>

<style scoped>
.shell {
  --sidebar-w: 232px;
  /* Sticky elements inside the page sit below the mobile top bar. */
  --topbar-h: 0px;

  display: grid;
  grid-template-columns: var(--sidebar-w) minmax(0, 1fr);
  min-height: 100dvh;
}

.shell[data-collapsed] {
  --sidebar-w: 64px;
}

.sidebar {
  position: sticky;
  top: 0;
  height: 100dvh;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 14px 12px;
  border-right: 1px solid var(--border);
  overflow: hidden auto;
}

.brand-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  min-height: var(--control-h);
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding-left: 4px;
  color: var(--text);
  text-decoration: none;
}

.brand:hover {
  text-decoration: none;
}

.brand-name {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: 600;
  letter-spacing: -0.01em;
  font-variation-settings: 'SHRP' 100;
}

.nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 10px;
  height: var(--control-h);
  padding: 0 10px;
  border-radius: var(--radius);
  color: var(--text-muted);
  font-weight: 500;
  text-decoration: none;
  white-space: nowrap;
}

.nav-link:hover {
  background: var(--surface-muted);
  color: var(--text);
  text-decoration: none;
}

.nav-link.router-link-active {
  background: var(--accent-soft);
  color: var(--accent);
}

.sidebar-foot {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.account {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 0 0 10px;
  border-top: 1px solid var(--border);
}

.email {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--text-muted);
  font-size: var(--text-xs);
}

/* Collapsed: icons only. */
.shell[data-collapsed] .sidebar {
  padding-inline: 10px;
}

.shell[data-collapsed] .sidebar .brand-row {
  flex-direction: column;
  gap: 10px;
}

.shell[data-collapsed] .sidebar .brand {
  padding-left: 0;
}

.shell[data-collapsed] .sidebar .brand-name,
.shell[data-collapsed] .sidebar .email {
  display: none;
}

/* Hidden from sight only: the label is still the link's accessible name. */
.shell[data-collapsed] .sidebar .nav-label {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
}

.shell[data-collapsed] .sidebar .nav-link {
  justify-content: center;
  padding: 0;
}

.shell[data-collapsed] .sidebar .account {
  justify-content: center;
  padding-left: 0;
}

.shell[data-collapsed] .sidebar .sidebar-running {
  justify-content: center;
  padding-inline: 0;
  flex-direction: column;
}

.content {
  min-width: 0;
  outline: none;
}

/* Off screen until a keyboard user tabs onto it. */
.skip-link {
  position: fixed;
  z-index: 60;
  top: 8px;
  left: 8px;
  padding: 8px 12px;
  border-radius: var(--radius);
  background: var(--accent);
  color: var(--accent-contrast);
  font-weight: 500;
  translate: 0 -200%;
}

.skip-link:focus {
  translate: 0 0;
}

.topbar {
  display: none;
}

/* The drawer is portaled, but its elements still carry this component's scope. */
.drawer-overlay {
  position: fixed;
  inset: 0;
  z-index: 40;
  background: var(--overlay);
}

.drawer-overlay[data-state='open'] {
  animation: ui-fade-in var(--dur) var(--ease);
}

.drawer {
  position: fixed;
  z-index: 41;
  inset: 0 auto 0 0;
  width: min(300px, 85vw);
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 10px 12px 16px;
  background: var(--bg);
  border-right: 1px solid var(--border);
  box-shadow: var(--shadow-float);
  outline: none;
}

.drawer[data-state='open'] {
  animation: drawer-in 200ms var(--ease);
}

.drawer-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-left: 6px;
}

.drawer .nav-link {
  height: 44px;
  gap: 12px;
  font-size: var(--text-md);
}

.drawer .email {
  font-size: var(--text-sm);
}

.drawer-account {
  margin-top: auto;
}

@keyframes drawer-in {
  from {
    translate: -100% 0;
  }
}

@media (width < 768px) {
  .shell,
  .shell[data-collapsed] {
    /* Icon button, 6px padding twice, 1px rule. */
    --topbar-h: calc(var(--control-h) + 13px);

    grid-template-columns: minmax(0, 1fr);
    grid-template-rows: auto 1fr;
  }

  .sidebar {
    display: none;
  }

  .topbar {
    position: sticky;
    top: 0;
    z-index: 20;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 8px;
    border-bottom: 1px solid var(--border);
    background: var(--bg);
  }

  .topbar .brand {
    padding-left: 0;
  }
}
</style>

