<template>
  <form
    id="editWorkspace"
    novalidate
    @submit.prevent="editOrganization"
    class="space-y-4"
  >
    <div class="text-xl flex flex-row gap-2 items-center">
      <div>
        {{ $t("message.page.workspace.forOrganization") }}
      </div>
      <div class="rounded-lg py-1 px-3 bg-bg-light">
        {{ organization.name }}
      </div>
    </div>
    <TextField
      :label="$t('message.page.workspace.workspaceName')"
      :placeholder="$t('message.page.workspace.enterWorkspaceName')"
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
      {{ model.id === null || model.id === undefined ? $t("message.common.create") : $t("message.common.save") }}
    </Button>
  </form>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { helpers, required } from '@vuelidate/validators';
import useVuelidate from '@vuelidate/core';
import { useWorkspaces } from '@/stores/workspaces';
import TextField from '@/components/ui/TextField.vue';
import Button from '@/components/ui/Button.vue';
import { reactive, ref, type PropType } from 'vue';
import type { OrganizationModel } from '@/stores/models/organization';

const props = defineProps({
  organization: {
    type: Object as PropType<OrganizationModel>,
    required: true,
  }
})

const model = defineModel({default: {
  id: null as null | number,
  name: "",
}})

const emit = defineEmits(["updated"])

const { t } = useI18n()

const workspaces = useWorkspaces()

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
    if (model.value.id === null || model.value.id === undefined) {
      await workspaces.createWorkspace(model.value.name, props.organization.organization_id)
      model.value.name = ""
    } else {
      await workspaces.updateWorkspace({workspace_id: model.value.id, name: model.value.name})
    }
    emit("updated")
  } finally {
    loading.value = false
  }
}
</script>

