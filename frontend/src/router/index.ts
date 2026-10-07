import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

import { i18n } from '@/i18n'
import { useAuthStore } from '@/stores/auth'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    guestOnly?: boolean
    /** Chrome around the page; App.vue picks it. Without one the page is bare. */
    layout?: 'app' | 'auth'
    /** Locale key of the page name shown in the browser tab. */
    titleKey?: string
  }
}

const routes: RouteRecordRaw[] = [
  { path: '/', redirect: { name: 'timer' } },
  {
    path: '/timer',
    name: 'timer',
    component: () => import('@/views/TimerView.vue'),
    meta: { requiresAuth: true, layout: 'app', titleKey: 'nav.timer' },
  },
  {
    path: '/projects',
    name: 'projects',
    component: () => import('@/views/ProjectsView.vue'),
    meta: { requiresAuth: true, layout: 'app', titleKey: 'nav.projects' },
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('@/views/SettingsView.vue'),
    meta: { requiresAuth: true, layout: 'app', titleKey: 'nav.settings' },
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { guestOnly: true, layout: 'auth', titleKey: 'auth.signIn.title' },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/views/RegisterView.vue'),
    meta: { guestOnly: true, layout: 'auth', titleKey: 'auth.signUp.title' },
  },
  { path: '/:pathMatch(.*)*', redirect: { name: 'timer' } },
]

// Component showcase for working on the UI kit. The branch is dropped from
// production builds together with the lazy chunk.
if (import.meta.env.DEV) {
  routes.unshift({
    path: '/dev/ui',
    name: 'dev-ui',
    component: () => import('@/views/DevUiView.vue'),
  })
}

export const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  // Validates the stored token against the API once per page load.
  await auth.restore()

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.meta.guestOnly && auth.isAuthenticated) {
    return { name: 'timer' }
  }
  return true
})

router.afterEach((to) => {
  const name = i18n.global.t('app.name')
  document.title = to.meta.titleKey ? `${i18n.global.t(to.meta.titleKey)} - ${name}` : name
})
