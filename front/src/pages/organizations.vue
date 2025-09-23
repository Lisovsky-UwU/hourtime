<template>
  <div>
    <div class="flex p-3">
      <div class="text-2xl">
        {{ $t("message.page.organization.title") }}
      </div>
      <div class="flex-grow"/>
      <Button
        second
        class=""
      >
        {{ $t("message.common.create") }}
      </Button>
    </div>

    <div class="border-t border-border">
      <OrganizationList />
    </div>
  </div>
</template>

<script setup lang="ts">
import Button from '@/components/ui/Button.vue';
import OrganizationList from '@/components/organization/OrganizationList/index.vue'
</script>
