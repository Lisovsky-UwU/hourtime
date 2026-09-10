<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import { useAsyncAction } from '@/composables/useApiError'
import { useAuthStore } from '@/stores/auth'

const PASSWORD_MIN_LENGTH = 10

const { t } = useI18n()
const auth = useAuthStore()
const router = useRouter()
const { busy, error, run } = useAsyncAction()

const email = ref('')
const password = ref('')

async function submit() {
  // Registration signs the new account in, so there is nothing else to do here.
  const done = await run(async () => {
    await auth.signUp(email.value, password.value)
    return true
  })
  if (done) await router.replace({ name: 'timer' })
}
</script>

<template>
  <div class="auth-page">
    <form class="card auth-card stack" @submit.prevent="submit">
      <div>
        <h1>{{ t('app.name') }}</h1>
        <p class="muted small">{{ t('app.tagline') }}</p>
      </div>

      <h2>{{ t('auth.signUp.title') }}</h2>

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
          autocomplete="new-password"
          :minlength="PASSWORD_MIN_LENGTH"
          required
        />
        <p class="muted small hint">
          {{ t('auth.fields.passwordHint', { min: PASSWORD_MIN_LENGTH }) }}
        </p>
      </div>

      <p v-if="error" class="banner">{{ error }}</p>

      <button type="submit" class="btn-primary" :disabled="busy">
        {{ busy ? t('common.loading') : t('auth.signUp.submit') }}
      </button>

      <p class="muted small centered">
        {{ t('auth.signUp.haveAccount') }}
        <RouterLink :to="{ name: 'login' }">{{ t('auth.signUp.signIn') }}</RouterLink>
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

.hint {
  margin: 4px 0 0;
}

.centered {
  text-align: center;
  margin: 0;
}
</style>
