/**
 * plugins/index.ts
 *
 * Automatically included in `./src/main.ts`
 */

// Plugins
import pinia from '../stores'
import router from '../router'
import i18n from './i18n'
import Notifications from '@kyvg/vue3-notification'

// Types
import type { App } from 'vue'

export function registerPlugins (app: App) {
  app
    .use(router)
    .use(pinia)
    .use(i18n)
    .use(Notifications)
}
