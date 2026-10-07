<script setup lang="ts">
import { ref, useId } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import UiButton from '@/components/ui/UiButton.vue'
import UiField from '@/components/ui/UiField.vue'
import UiInput from '@/components/ui/UiInput.vue'
import { useAsyncAction } from '@/composables/useApiError'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const { busy, error, run } = useAsyncAction()
const errorId = useId()

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
  <form class="auth-form" @submit.prevent="submit">
    <h1>{{ t('auth.signIn.title') }}</h1>

    <UiField :label="t('auth.fields.email')">
      <UiInput
        v-model="email"
        type="email"
        autocomplete="username"
        required
        :invalid="!!error"
        :aria-describedby="error ? errorId : undefined"
      />
    </UiField>

    <UiField :label="t('auth.fields.password')">
      <UiInput
        v-model="password"
        type="password"
        autocomplete="current-password"
        required
        :invalid="!!error"
        :aria-describedby="error ? errorId : undefined"
      />
    </UiField>

    <p v-if="error" :id="errorId" class="form-error" role="alert">{{ error }}</p>

    <UiButton type="submit" variant="primary" class="submit" :disabled="busy">
      {{ busy ? t('auth.signIn.busy') : t('auth.signIn.submit') }}
    </UiButton>

    <p class="switch muted">
      {{ t('auth.signIn.noAccount') }}
      <RouterLink :to="{ name: 'register' }">{{ t('auth.signIn.createOne') }}</RouterLink>
    </p>
  </form>
</template>

<style scoped>
.auth-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.auth-form h1 {
  font-size: var(--text-lg);
}

.form-error {
  color: var(--danger);
}

.submit {
  width: 100%;
}

.switch {
  text-align: center;
}
</style>
