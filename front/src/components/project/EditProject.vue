<template>
  <form
    id="editProject"
    novalidate
    @submit.prevent="editProject"
    class="space-y-4"
  >
    <div class="flex flex-row gap-3 items-center">
      <ColorPicker v-model="newData.color"/>

      <TextField
        class="flex-grow"
        :placeholder="$t('message.page.project.enterProjectName')"
        :error="v$.name.$error"
        :errorsText="v$.name.$errors.map((error) => error.$message)"
        :loading="loading"
        v-model="newData.name"
        @change="v$.name.$validate()"
      />
    </div>
    <TextArea
      :label="$t('message.page.project.projectDescription')"
      :placeholder="$t('message.page.project.enterProjectDescription')"
      :loading="loading"
      v-model="newData.description"
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
import TextField from '@/components/ui/TextField.vue';
import TextArea from '../ui/TextArea.vue';
import Button from '@/components/ui/Button.vue';
import { reactive, ref } from 'vue';
import { useProjects } from '@/stores/projects';
import ColorPicker from './ColorPicker.vue';


const model = defineModel({default: {
  id: null as null | number,
  name: "",
  description: null as null | string,
  color: null as null | string,
}})

const emit = defineEmits(["updated"])

const { t } = useI18n()

const projects = useProjects()

const loading = ref(false)

const newData = reactive(model.value)

const rules = {
  name: {
    required: helpers.withMessage(t("message.validations.fieldIsRequired"), required),
  }
}

const v$ = useVuelidate(rules, newData)

async function editProject() {
  await v$.value.$validate()
  if (v$.value.$error) {
    return
  }
  loading.value = true
  try {
    if (model.value.id === null || model.value.id === undefined) {
      await projects.createProject(newData)
    } else {
      await projects.updateProject({
        project_id: model.value.id,
        name: newData.name,
        description: newData.description,
        color: newData.color,
      })
    }
    emit("updated")
  } finally {
    loading.value = false
  }
}
</script>

