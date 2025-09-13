<template>
  <OrganizationElement
    v-for="organization of organizations.organizations"
    :key="organization.id"
    :organization="organization"
  />
</template>

<script setup lang="ts">
import { useOrganizations } from '@/stores/organizations';
import OrganizationElement from './OrganizationElement.vue';

const organizations = useOrganizations()
</script>
