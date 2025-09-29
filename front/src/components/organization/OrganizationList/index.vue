<template>
  <OrganizationElement
    v-for="organization of organizations.organizations"
    :key="organization.organization_id"
    :organization="organization"
    @edit-organization="doEditOrganization"
    @delete-organization="doDeleteOrganization"
    @add-workspace="doAddWorkspace"
    @edit-workspace="doEditWorkspace"
    @delete-workspace="doDeleteWorkspace"
  />

  <!-- Organization dialogs -->
  <Dialog v-model="showEditOrganizationDialog">
    <div class="flex flex-col gap-4">
      <EditOrganization
        v-model="currentEditOrganization.organizationData"
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
          {{ currentEditOrganization.organizationData?.name }}
        </div>

        <div class="mt-4 flex flex-col">
          <div>
            {{ $t("message.page.organization.workspaces") }}:
          </div>
          <div
            v-for="workspace in currentEditOrganization.organizationData?.workspaces"
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

  <!-- Workspace dialogs -->
  <Dialog v-model="showEditWorkspaceDialog">
    <div class="flex flex-col gap-4">
      <EditWorkspace
        v-model="currentEditWorkspace.workspaceData"
        :organization="currentEditWorkspace.organizationData"
        @updated="workspaceUpdated"
      />
      <Button
        block
        @click="showEditWorkspaceDialog = false"
      >
        {{ $t("message.common.cancel") }}
      </Button>
    </div>
  </Dialog>

  <Dialog v-model="showDeleteWorkspaceDialog">
    <div class="flex flex-col gap-4">
      <div class="text-xl">
        {{ $t("message.page.workspace.confirmDelete") }}
      </div>
      <div class="flex flex-row text-lg">
        <div>
          {{ $t("message.page.workspace.forOrganization") }}:
        </div>

        <div class="ml-2 font-bold">
          {{ currentEditWorkspace.organizationData?.name }}
        </div>
      </div>

      <div class="p-4 rounded-lg bg-bg-light flex flex-col">
        <div>
          {{ currentEditWorkspace.workspaceData?.name }}
        </div>
      </div>

      <Button
        block
        color="danger"
        :loading="deleteWorkspaceLoading"
        @click="workspaceDelete"
      >
        {{ $t("message.common.delete") }}
      </Button>
      <Button
        block
        :disabled="deleteWorkspaceLoading"
        @click="showDeleteWorkspaceDialog = false"
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
import EditWorkspace from '@/components/workspace/EditWorkspace.vue';
import { reactive, ref } from 'vue';
import type { OrganizationModel } from '@/stores/models/organization';
import { useWorkspaces } from '@/stores/workspaces';
import type { WorkspaceModel } from '@/stores/models/workspace';

const organizations = useOrganizations()
const workspaces = useWorkspaces()

const currentEditOrganization = reactive({organizationData: null as null | OrganizationModel})
const showEditOrganizationDialog = ref(false)
const showDeleteOrganizationDialog = ref(false)

const deleteOrganizationLoading = ref(false)

function doEditOrganization(organization: OrganizationModel) {
  currentEditOrganization.organizationData = {
    organization_id: organization.organization_id,
    name: organization.name,
    workspaces: organization.workspaces,
    access: organization.access,
  }
  showEditOrganizationDialog.value = true
}

function doDeleteOrganization(organization: OrganizationModel) {
  currentEditOrganization.organizationData = organization
  showDeleteOrganizationDialog.value = true
}

async function organizationUpdated() {
  showEditOrganizationDialog.value = false
  await organizations.loadMyOrganizations()
}

async function organizationDelete() {
  if (currentEditOrganization.organizationData === null) {
    return
  }
  deleteOrganizationLoading.value = true
  try {
    await organizations.deleteOrganization(currentEditOrganization.organizationData.organization_id)
    showDeleteOrganizationDialog.value = false
    await organizations.loadMyOrganizations()
  } finally {
    deleteOrganizationLoading.value = false
  }
}


const currentEditWorkspace = reactive({
  workspaceData: null as null | WorkspaceModel,
  organizationData: null as null | OrganizationModel,
})
const showEditWorkspaceDialog = ref(false)
const showDeleteWorkspaceDialog = ref(false)

const deleteWorkspaceLoading = ref(false)

function doAddWorkspace(organization: OrganizationModel) {
  currentEditWorkspace.workspaceData = {id: null, name: ""}
  currentEditWorkspace.organizationData = organization
  showEditWorkspaceDialog.value = true
}

function doEditWorkspace(workspace: WorkspaceModel, organization: OrganizationModel) {
  currentEditWorkspace.workspaceData = {id: workspace.id, name: workspace.name}
  currentEditWorkspace.organizationData = organization
  showEditWorkspaceDialog.value = true
}

function doDeleteWorkspace(workspace: WorkspaceModel, organization: OrganizationModel) {
  currentEditWorkspace.workspaceData = workspace
  currentEditWorkspace.organizationData = organization
  showDeleteWorkspaceDialog.value = true
}

async function workspaceUpdated() {
  showEditWorkspaceDialog.value = false
  if (currentEditWorkspace.organizationData !== null) {
    await organizations.refreshWorkspaces(currentEditWorkspace.organizationData.organization_id)
  }
}

async function workspaceDelete() {
  if (currentEditWorkspace.workspaceData === null) {
    return
  }
  deleteWorkspaceLoading.value = true
  try {
    await workspaces.deleteWorkspace(currentEditWorkspace.workspaceData.id)

    showDeleteWorkspaceDialog.value = false
    if (currentEditWorkspace.organizationData !== null) {
      await organizations.refreshWorkspaces(currentEditWorkspace.organizationData.organization_id)
    }
  } finally {
    deleteWorkspaceLoading.value = false
  }
}
</script>
