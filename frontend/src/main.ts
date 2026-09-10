import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from '@/App.vue'
import { onTokensChanged } from '@/api/client'
import { applyInitialLocale, i18n } from '@/i18n'
import { router } from '@/router'
import '@/styles/main.css'

applyInitialLocale()

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

app.mount('#app')
