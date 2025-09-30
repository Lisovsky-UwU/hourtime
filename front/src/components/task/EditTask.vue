<template>
  <form
    id="editTask"
    novalidate
    @submit.prevent="editTask"
    class="space-y-4"
  >
    <div class="w-full p-2 text-center text-lg font-bold rounded-lg bg-bg-light">
      {{ model.id === null ? $t("message.page.task.newTask") : $t("message.page.task.taskNumber", {
      taskNumber: model.number}) }}
    </div>
    <TextField
      :label="$t('message.page.task.taskName')"
      :placeholder="$t('message.page.task.enterTaskName')"
      :error="v$.name.$error"
      :errorsText="v$.name.$errors.map((error) => error.$message)"
      :loading="loading"
      v-model="newData.name"
      @change="v$.name.$validate()"
    />
    <TextArea
      :label="$t('message.page.task.taskDescription')"
      :placeholder="$t('message.page.task.enterTaskDescription')"
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
import { useTasks } from '@/stores/tasks';
import { useProjects } from '@/stores/projects';


const model = defineModel({default: {
  id: null as null | string,
  number: null as null | number,
  name: "",
  description: null as null | string,
  project_id: null as null | number,
}})

const emit = defineEmits(["updated"])

const { t } = useI18n()

const tasks = useTasks()
const projects = useProjects()

const loading = ref(false)

const newData = reactive(model.value)

const rules = {
  name: {
    required: helpers.withMessage(t("message.validations.fieldIsRequired"), required),
  }
}

const v$ = useVuelidate(rules, newData)

async function editTask() {
  await v$.value.$validate()
  if (v$.value.$error) {
    return
  }
  loading.value = true
  try {
    if (model.value.id === null || model.value.id === undefined) {
      await tasks.createTask(newData)
    } else {
      await tasks.updateTask({
        task_id: model.value.id,
        project_id: model.value.project_id,
        name: newData.name,
        description: newData.description,
      })
    }
    emit("updated")
  } finally {
    loading.value = false
  }
}
</script>

