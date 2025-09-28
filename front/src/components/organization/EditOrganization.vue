<template>
  <form
    id="newOrganization"
    novalidate
    @submit.prevent="editOrganization"
    class="space-y-4"
  >
    <TextField
      :label="$t('message.page.organization.organizationName')"
      :placeholder="$t('message.page.organization.enterOrganizationName')"
      :error="v$.name.$error"
      :errorsText="v$.name.$errors.map((error) => error.$message)"
      :loading="loading"
      v-model="newData.name"
      @change="v$.name.$validate()"
    />
    <Button
      block
      color="primary"
      type="submit"
      :loading="loading"
    >
      {{ model.organization_id === null || model.organization_id === undefined ? $t("message.common.create") : $t("message.common.save") }}
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

const model = defineModel({default: {
  organization_id: null as null | number,
  name: "",
}})

const emit = defineEmits(["updated"])

const { t } = useI18n()

const organizations = useOrganizations()

const loading = ref(false)

const newData = reactive(model.value)

const rules = {
  name: {
    required: helpers.withMessage(t("message.validations.fieldIsRequired"), required),
  }
}

const v$ = useVuelidate(rules, newData)

async function editOrganization() {
  await v$.value.$validate()
  if (v$.value.$error) {
    return
  }
  loading.value = true
  try {
    if (model.value.organization_id === null || model.value.organization_id === undefined) {
      await organizations.createOrganization(model.value.name)
      model.value.name = ""
    } else {
      await organizations.updateOrganization(model.value)
    }
    emit("updated")
  } finally {
    loading.value = false
  }
}
</script>
