<template>
  <form
    id="newOrganization"
    novalidate
    @submit.prevent="createNewOrganization"
    class="space-y-4"
  >
    <TextField
      :label="$t('message.page.organization.organizationName')"
      :placeholder="$t('message.page.organization.enterOrganizationName')"
      :error="v$.name.$error"
      :errorsText="v$.name.$errors.map((error) => error.$message)"
      :loading="loading"
      v-model="newOrganizationName.name"
      @change="v$.name.$validate()"
    />
    <Button
      block
      type="submit"
      :loading="loading"
    >
      {{ $t("message.common.create") }}
    </Button>
  </form>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { helpers, required } from '@vuelidate/validators';
import useVuelidate from '@vuelidate/core';
import { useOrganizations } from '@/stores/organizations';
import TextField from '@/components/ui/TextField.vue';
import Button from '@/components/ui/Button.vue';
import { reactive, ref } from 'vue';

const props = defineProps({
  defaultName: {
    type: String,
    default: "",
  }
})

const emit = defineEmits(["created"])

const { t } = useI18n()

const organizations = useOrganizations()

const loading = ref(false)

const newOrganizationName = reactive({
  name: props.defaultName,
})

const rules = {
  name: {
    required: helpers.withMessage(t("message.validations.fieldIsRequired"), required),
  }
}

const v$ = useVuelidate(rules, newOrganizationName)

async function createNewOrganization() {
  loading.value = true
  try {
    await organizations.createOrganization(newOrganizationName.name)
    emit("created")
  } finally {
    loading.value = false
  }
}
</script>
