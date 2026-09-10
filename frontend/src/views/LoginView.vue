<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import { useAsyncAction } from '@/composables/useApiError'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const { busy, error, run } = useAsyncAction()

const email = ref('')
const password = ref('')

async function submit() {
  const done = await run(async () => {
    await auth.signIn(email.value, password.value)
    return true
  })
  if (!done) return
  const redirect = route.query.redirect
  await router.replace(typeof redirect === 'string' ? redirect : { name: 'timer' })
}
</script>

<template>
  <div class="auth-page">
    <form class="card auth-card stack" @submit.prevent="submit">
      <div>
        <h1>{{ t('app.name') }}</h1>
        <p class="muted small">{{ t('app.tagline') }}</p>
      </div>

      <h2>{{ t('auth.signIn.title') }}</h2>

      <div class="field">
        <label for="email">{{ t('auth.fields.email') }}</label>
        <input id="email" v-model="email" type="email" autocomplete="username" required />
      </div>

      <div class="field">
        <label for="password">{{ t('auth.fields.password') }}</label>
        <input
          id="password"
          v-model="password"
          type="password"
          autocomplete="current-password"
          required
        />
      </div>

      <p v-if="error" class="banner">{{ error }}</p>

      <button type="submit" class="btn-primary" :disabled="busy">
        {{ busy ? t('common.loading') : t('auth.signIn.submit') }}
      </button>

      <p class="muted small centered">
        {{ t('auth.signIn.noAccount') }}
        <RouterLink :to="{ name: 'register' }">{{ t('auth.signIn.createOne') }}</RouterLink>
      </p>
    </form>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px 16px;
}

.auth-card {
  width: min(400px, 100%);
  padding: 24px;
}

.centered {
  text-align: center;
  margin: 0;
}
</style>
