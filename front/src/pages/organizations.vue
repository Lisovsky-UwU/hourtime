<template>
  <div>
    <div class="flex p-3">
      <div class="text-2xl">
        {{ $t("message.page.organization.title") }}
      </div>
      <div class="flex-grow"/>
      <Button
        @click="showCreateDialog = true"
      >
        <svg-icon type="mdi" :path="mdiPlus" />
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
      >
        {{ $t("message.common.cancel") }}
      </Button>
    </div>
  </Dialog>
</template>

<script setup lang="ts">
import Button from '@/components/ui/Button.vue';
import Dialog from '@/components/ui/Dialog.vue';
import SvgIcon from '@jamescoyle/vue-icon'
import OrganizationList from '@/components/organization/OrganizationList/index.vue'
import EditOrganization from '@/components/organization/EditOrganization.vue';
import { ref } from 'vue';
import { useOrganizations } from '@/stores/organizations';
import { mdiPlus } from '@mdi/js';

const showCreateDialog = ref(false)

const organizations = useOrganizations()

async function createdOrganization() {
  showCreateDialog.value = false
  await organizations.loadMyOrganizations()
}
</script>
