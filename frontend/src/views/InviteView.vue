<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import * as workspacesApi from '@/api/workspaces'
import UiButton from '@/components/ui/UiButton.vue'
import { useAsyncAction } from '@/composables/useApiError'
import { useAuthStore } from '@/stores/auth'
import type { InvitePreview } from '@/types'
import { clearPendingInvite, pendingInvite } from '@/utils/invite'

const { t } = useI18n()
const auth = useAuthStore()
const { busy, error, run } = useAsyncAction()

const token = pendingInvite()
const preview = ref<InvitePreview | null>(null)
const invalid = ref(!token)

async function join() {
  if (!token) return
  const done = await run(async () => {
    await workspacesApi.acceptInvite(token)
    return true
  })
  if (done) {
    clearPendingInvite()
    // A full load: the tab picks its workspace on sign-in, and that is now the new one.
    window.location.assign('/timer')
  }
}

onMounted(async () => {
  if (!token) return
  try {
    preview.value = await workspacesApi.previewInvite(token)
  } catch {
    invalid.value = true
    clearPendingInvite()
  }
})
</script>

<template>
  <div class="invite">
    <h1>{{ t('invite.title') }}</h1>

    <p v-if="invalid" class="muted">{{ t('invite.invalid') }}</p>

    <template v-else-if="preview">
      <p>
        {{ t('invite.from', { name: preview.invited_by, workspace: preview.workspace_name }) }}
      </p>

      <template v-if="auth.isAuthenticated">
        <p class="muted">{{ t('invite.signedInAs', { email: auth.user?.email ?? '' }) }}</p>
        <p v-if="error" class="form-error" role="alert">{{ error }}</p>
        <UiButton variant="primary" class="submit" :disabled="busy" @click="join">
          {{ t('invite.join', { workspace: preview.workspace_name }) }}
        </UiButton>
      </template>

      <template v-else>
        <UiButton
          variant="primary"
          class="submit"
          @click="$router.push({ name: 'register' })"
        >
          {{ t('invite.register') }}
        </UiButton>
        <p class="switch muted">
          {{ t('auth.signUp.haveAccount') }}
          <RouterLink :to="{ name: 'login', query: { redirect: '/invite' } }">
            {{ t('auth.signUp.signIn') }}
          </RouterLink>
        </p>
      </template>
    </template>

    <p v-else class="muted" role="status">{{ t('common.loading') }}</p>
  </div>
</template>

<style scoped>
.invite {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.invite h1 {
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
