<template>
  <div>
    <div class="flex p-3">
      <div class="text-2xl">
        {{ $t("message.page.organization.title") }}
      </div>
      <div class="flex-grow"/>
      <Button
        color="second"
        @click="showCreateDialog = true"
      >
        {{ $t("message.common.create") }}
      </Button>
    </div>

    <div class="border-t border-border">
      <OrganizationList />
    </div>
  </div>

  <Dialog v-model="showCreateDialog">
    <div class="flex flex-col gap-4">
      <EditOrganization
        @updated="createdOrganization"
      />
      <Button
        block
        @click="showCreateDialog = false"
      >Cancel</Button>
    </div>
  </Dialog>
</template>

<script setup lang="ts">
import Button from '@/components/ui/Button.vue';
import Dialog from '@/components/ui/Dialog.vue';
import OrganizationList from '@/components/organization/OrganizationList/index.vue'
import EditOrganization from '@/components/organization/EditOrganization.vue';
import { ref } from 'vue';
import { useOrganizations } from '@/stores/organizations';

const showCreateDialog = ref(false)

const organizations = useOrganizations()

async function createdOrganization() {
  showCreateDialog.value = false
  await organizations.loadMyOrganizations()
}
</script>
