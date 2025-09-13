<template>
  <div v-if="loading" class="h-screen flex justify-center items-center">
    <Loader />
  </div>

  <div v-else-if="organizations.myOrganizations.length === 0" class="h-screen flex justify-center
    items-center">
    <div class="card w-[400px]">
      <div class="p-4">
        <div class="text-xl mb-4 flex justify-center">
          {{ $t("message.page.organization.createNewOrganization") }}
        </div>
        <div>
          <CreateOrganization
            :default-name="$t('message.page.organization.defaultName', {userName:
              userData.currentUserData.display_name})"
            @created="reloadOrganizations"
          />
        </div>
      </div>
    </div>
  </div>

  <div v-else class="h-screen">
    <AppBar/>
    <div class="overflow-y-auto" style="max-height: calc(100vh - 60px)">
      <slot />
    </div>
  </div>
</template>

<script setup>
import { useOrganizations } from '@/stores/organizations';
import { onMounted, ref } from 'vue';
import Loader from '@/components/ui/Loader.vue';
import { useUserData } from '@/stores/user-data';
import { useI18n } from 'vue-i18n';
import CreateOrganization from '@/components/organization/CreateOrganization.vue';
import AppBar from '@/components/AppBar.vue';

const loading = ref(true)

const { t } = useI18n()
const organizations = useOrganizations()
const userData = useUserData()

async function reloadOrganizations() {
  loading.value = true
  try {
    await organizations.loadMyOrganizations()
  } finally {
    loading.value = false
  }
}

onMounted(reloadOrganizations)
</script>
