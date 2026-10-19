<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import * as workspacesApi from '@/api/workspaces'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import UiButton from '@/components/ui/UiButton.vue'
import type { MenuEntry } from '@/components/ui/UiDropdownMenu.vue'
import UiDropdownMenu from '@/components/ui/UiDropdownMenu.vue'
import UiIconButton from '@/components/ui/UiIconButton.vue'
import UiInput from '@/components/ui/UiInput.vue'
import { toast } from '@/components/ui/toast'
import { messageFor } from '@/composables/useApiError'
import { useAuthStore } from '@/stores/auth'
import { useWorkspaceStore } from '@/stores/workspace'
import type { Invite, Member } from '@/types'
import { inviteLink } from '@/utils/invite'

const { t, locale } = useI18n()
const auth = useAuthStore()
const workspace = useWorkspaceStore()

const members = ref<Member[]>([])
const invites = ref<Invite[]>([])
const loaded = ref(false)
const loadError = ref<string | null>(null)
/** The link just made: the server keeps only a digest, so it is shown once. */
const issued = ref<string | null>(null)
const pendingRemove = ref<Member | null>(null)
const busy = ref(false)

const isAdmin = computed(() => workspace.item?.role === 'admin')
const leaving = computed(() => pendingRemove.value?.user_id === auth.user?.id)

function nameOf(member: Member): string {
  return member.display_name || member.email
}

function roleLabel(member: Member): string {
  if (member.is_owner) return t('members.roles.owner')
  return member.role === 'admin' ? t('members.roles.admin') : t('members.roles.member')
}

function day(iso: string): string {
  return new Date(iso).toLocaleDateString(locale.value, { day: 'numeric', month: 'long' })
}

async function load() {
  loadError.value = null
  try {
    await workspace.load()
    const [found, open] = await Promise.all([
      workspacesApi.members(),
      isAdmin.value ? workspacesApi.invites() : Promise.resolve([]),
    ])
    members.value = found
    invites.value = open
    loaded.value = true
  } catch (cause) {
    loadError.value = messageFor(cause)
  }
}

async function attempt(action: () => Promise<unknown>) {
  busy.value = true
  try {
    await action()
  } catch (cause) {
    toast.error(messageFor(cause))
  } finally {
    busy.value = false
  }
}

function invite() {
  return attempt(async () => {
    const created = await workspacesApi.createInvite()
    issued.value = inviteLink(created.token)
    invites.value = [created, ...invites.value]
  })
}

function copyLink() {
  if (!issued.value) return
  navigator.clipboard
    .writeText(issued.value)
    .then(() => toast.success(t('members.copied')))
    .catch(() => toast.error(t('members.copyFailed')))
}

function revoke(item: Invite) {
  return attempt(async () => {
    await workspacesApi.revokeInvite(item.id)
    invites.value = invites.value.filter((other) => other.id !== item.id)
    issued.value = null
  })
}

function setRole(member: Member, role: Member['role']) {
  return attempt(async () => {
    await workspacesApi.setRole(member.user_id, role)
    member.role = role
  })
}

function confirmRemove() {
  const member = pendingRemove.value
  if (!member) return
  return attempt(async () => {
    await workspacesApi.removeMember(member.user_id)
    if (leaving.value) {
      // Back to the user's own workspace: a full load picks it up from the profile.
      window.location.assign('/timer')
      return
    }
    members.value = members.value.filter((other) => other.user_id !== member.user_id)
    pendingRemove.value = null
  })
}

function menuFor(member: Member): MenuEntry[] {
  if (member.user_id === auth.user?.id) {
    return [
      {
        label: t('members.leave'),
        icon: 'sign-out',
        variant: 'danger',
        select: () => (pendingRemove.value = member),
      },
    ]
  }
  return [
    member.role === 'admin'
      ? { label: t('members.makeMember'), select: () => void setRole(member, 'member') }
      : { label: t('members.makeAdmin'), select: () => void setRole(member, 'admin') },
    'separator',
    {
      label: t('members.remove'),
      icon: 'trash',
      variant: 'danger',
      select: () => (pendingRemove.value = member),
    },
  ]
}

/** The owner has no actions; admins act on others, everyone may leave. */
function hasMenu(member: Member): boolean {
  if (member.is_owner) return false
  return isAdmin.value || member.user_id === auth.user?.id
}

onMounted(load)
</script>

<template>
  <div class="page list-page">
    <header class="page-head">
      <h1>{{ t('members.title') }}</h1>
      <UiButton v-if="isAdmin" variant="primary" icon="plus" :disabled="busy" @click="invite">
        {{ t('members.invite') }}
      </UiButton>
    </header>

    <div v-if="loadError" class="alert" role="alert">
      <span>{{ t('members.loadFailed') }} {{ loadError }}</span>
      <UiButton size="sm" @click="load">{{ t('common.retry') }}</UiButton>
    </div>

    <section v-if="issued" class="sheet issued" aria-live="polite">
      <p>{{ t('members.issuedHint') }}</p>
      <div class="issued-row">
        <UiInput :model-value="issued" readonly :aria-label="t('members.link')" />
        <UiButton icon="copy" @click="copyLink">{{ t('members.copy') }}</UiButton>
      </div>
    </section>

    <table v-if="loaded" class="sheet data-table">
      <thead>
        <tr>
          <th scope="col">{{ t('members.name') }}</th>
          <th scope="col">{{ t('members.role') }}</th>
          <th scope="col" class="actions-col">
            <span class="visually-hidden">{{ t('ui.more') }}</span>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="member in members" :key="member.user_id">
          <td>
            <span class="row-name">
              <span class="row-name-text">{{ nameOf(member) }}</span>
            </span>
            <span v-if="member.display_name" class="muted email">{{ member.email }}</span>
          </td>
          <td class="role">{{ roleLabel(member) }}</td>
          <td class="actions-col">
            <UiDropdownMenu
              v-if="hasMenu(member)"
              :items="menuFor(member)"
              :label="t('members.actionsFor', { name: nameOf(member) })"
            />
          </td>
        </tr>
      </tbody>
    </table>

    <template v-if="isAdmin && invites.length">
      <h2 class="sub-head">{{ t('members.openLinks') }}</h2>
      <table class="sheet data-table">
        <tbody>
          <tr v-for="item in invites" :key="item.id">
            <td>{{ t('members.linkMade', { day: day(item.created_at) }) }}</td>
            <td class="muted">{{ t('members.linkExpires', { day: day(item.expires_at) }) }}</td>
            <td class="actions-col">
              <UiIconButton
                icon="trash"
                variant="danger"
                :label="t('members.revoke')"
                :disabled="busy"
                @click="revoke(item)"
              />
            </td>
          </tr>
        </tbody>
      </table>
    </template>

    <ConfirmDialog
      :open="pendingRemove !== null"
      :title="
        leaving
          ? t('members.leaveTitle', { workspace: workspace.item?.name ?? '' })
          : t('members.removeTitle', { name: pendingRemove ? nameOf(pendingRemove) : '' })
      "
      :message="leaving ? t('members.leaveConfirm') : t('members.removeConfirm')"
      :confirm-label="leaving ? t('members.leave') : t('members.remove')"
      :busy="busy"
      @close="pendingRemove = null"
      @confirm="confirmRemove"
    />
  </div>
</template>

<style scoped>
.issued {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
}

.issued-row {
  display: flex;
  gap: 8px;
}

.issued-row :deep(input) {
  flex: 1;
  min-width: 0;
}

.email {
  display: block;
  font-size: var(--text-sm);
}

.role {
  white-space: nowrap;
}

.sub-head {
  margin-top: 8px;
  font-size: var(--text-md);
}
</style>
