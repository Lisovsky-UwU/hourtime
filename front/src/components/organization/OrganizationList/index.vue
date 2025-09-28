<template>
  <OrganizationElement
    v-for="organization of organizations.organizations"
    :key="organization.organization_id"
    :organization="organization"
    @edit-organization="doEditOrganization"
    @delete-organization="doDeleteOrganization"
  />

  <Dialog v-model="showEditOrganizationDialog">
    <div class="flex flex-col gap-4">
      <EditOrganization
        v-model="currentEditOrganization.organization_data"
        @updated="organizationUpdated"
      />
      <Button
        block
        @click="showEditOrganizationDialog = false"
      >
        {{ $t("message.common.cancel") }}
      </Button>
    </div>
  </Dialog>

  <Dialog v-model="showDeleteOrganizationDialog">
    <div class="flex flex-col gap-4">
      <div class="text-xl">
        {{ $t("message.page.organization.confirmDelete") }}
      </div>

      <div class="p-4 rounded-lg bg-bg-light flex flex-col">
        <div class="font-bold">
          {{ currentDeleteOrganization.organization_data?.name }}
        </div>

        <div class="mt-4 flex flex-col">
          <div>
            {{ $t("message.page.organization.workspaces") }}:
          </div>
          <div
            v-for="workspace in currentDeleteOrganization.organization_data?.workspaces"
            :key="workspace.id"
            class="ml-4"
          >
            {{ workspace.name }}
          </div>
        </div>
      </div>

      <Button
        block
        color="danger"
        :loading="deleteOrganizationLoading"
        @click="organizationDelete"
      >
        {{ $t("message.common.delete") }}
      </Button>
      <Button
        block
        :disabled="deleteOrganizationLoading"
        @click="showDeleteOrganizationDialog = false"
      >
        {{ $t("message.common.cancel") }}
      </Button>
    </div>
  </Dialog>
</template>

<script setup lang="ts">
import { useOrganizations } from '@/stores/organizations';
import OrganizationElement from './OrganizationElement.vue';
import Dialog from '@/components/ui/Dialog.vue';
import Button from '@/components/ui/Button.vue';
import EditOrganization from '../EditOrganization.vue';
import { reactive, ref } from 'vue';
import type { OrganizationModel } from '@/stores/models/organization';

const organizations = useOrganizations()

const currentEditOrganization = reactive({organization_data: null as null | OrganizationModel})
const currentDeleteOrganization = reactive({organization_data: null as null | OrganizationModel})
const showEditOrganizationDialog = ref(false)
const showDeleteOrganizationDialog = ref(false)

const deleteOrganizationLoading = ref(false)

function doEditOrganization(organization: OrganizationModel) {
  currentEditOrganization.organization_data = organization
  showEditOrganizationDialog.value = true
}

function doDeleteOrganization(organization: OrganizationModel) {
  currentDeleteOrganization.organization_data = organization
  showDeleteOrganizationDialog.value = true
}

async function organizationUpdated() {
  showEditOrganizationDialog.value = false
  await organizations.loadMyOrganizations()
}

async function organizationDelete() {
  if (currentDeleteOrganization.organization_data === null) {
    return
  }
  deleteOrganizationLoading.value = true
  try {
    await organizations.deleteOrganization(currentDeleteOrganization.organization_data.organization_id)
    showDeleteOrganizationDialog.value = false
    await organizations.loadMyOrganizations()
  } finally {
    deleteOrganizationLoading.value = false
  }
}
</script>
