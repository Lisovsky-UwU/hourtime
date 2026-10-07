import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from '@/App.vue'
import { onTokensChanged } from '@/api/client'
import { i18n, installInitialLocale } from '@/i18n'
import { router } from '@/router'
import '@fontsource-variable/geologica/shrp.css'
import '@/styles/tokens.css'
import '@/styles/base.css'
import '@/styles/utilities.css'
import '@/styles/floating.css'

const app = createApp(App)
app.use(createPinia())
app.use(i18n)
app.use(router)

// A refresh that fails clears the tokens from anywhere in the app; make sure
// the user lands on the sign-in page instead of a half-dead screen.
onTokensChanged((tokens) => {
  if (!tokens && router.currentRoute.value.meta.requiresAuth) {
    void router.replace({ name: 'login', query: { redirect: router.currentRoute.value.fullPath } })
  }
})

// The language is settled first, so nothing renders in English for a moment.
void installInitialLocale().then(() => app.mount('#app'))
