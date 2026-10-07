<script setup lang="ts">
import { ref, useId } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import UiButton from '@/components/ui/UiButton.vue'
import UiField from '@/components/ui/UiField.vue'
import UiInput from '@/components/ui/UiInput.vue'
import { useAsyncAction } from '@/composables/useApiError'
import { useAuthStore } from '@/stores/auth'

const PASSWORD_MIN_LENGTH = 10

const { t } = useI18n()
const auth = useAuthStore()
const router = useRouter()
const { busy, error, run } = useAsyncAction()
const errorId = useId()

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
  <form class="auth-form" @submit.prevent="submit">
    <h1>{{ t('auth.signUp.title') }}</h1>

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

    <UiField
      :label="t('auth.fields.password')"
      :hint="t('auth.fields.passwordHint', { min: PASSWORD_MIN_LENGTH })"
    >
      <UiInput
        v-model="password"
        type="password"
        autocomplete="new-password"
        :minlength="PASSWORD_MIN_LENGTH"
        required
        :invalid="!!error"
        :aria-describedby="error ? errorId : undefined"
      />
    </UiField>

    <p v-if="error" :id="errorId" class="form-error" role="alert">{{ error }}</p>

    <UiButton type="submit" variant="primary" class="submit" :disabled="busy">
      {{ busy ? t('auth.signUp.busy') : t('auth.signUp.submit') }}
    </UiButton>

    <p class="switch muted">
      {{ t('auth.signUp.haveAccount') }}
      <RouterLink :to="{ name: 'login' }">{{ t('auth.signUp.signIn') }}</RouterLink>
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
