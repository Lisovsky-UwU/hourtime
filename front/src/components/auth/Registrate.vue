<template>
  <form
    id="loginForm"
    class="space-y-4 flex flex-col flex-grow"
    novalidate
    @submit.prevent="handleSubmit"
  >
    <TextField
      id="username"
      :label="$t('message.page.auth.username')"
      :placeholder="$t('message.page.auth.enterUsername')"
      :error="v$.username.$error"
      :errorsText="v$.username.$errors.map((error) => error.$message)"
      :loading="loadingRegistrate"
      v-model="registrationData.username"
      @change="v$.username.$validate()"
    />
    <TextField
      id="displayName"
      :label="$t('message.page.auth.displayName')"
      :placeholder="$t('message.page.auth.enterDisplayName')"
      :error="v$.displayName.$error"
      :errorsText="v$.displayName.$errors.map((error) => error.$message)"
      :loading="loadingRegistrate"
      v-model="registrationData.displayName"
      @change="v$.displayName.$validate()"
    />
    <TextField
      id="password"
      type="password"
      :label="$t('message.page.auth.password')"
      :placeholder="$t('message.page.auth.enterPassword')"
      :error="v$.password.$error"
      :errorsText="v$.password.$errors.map((error) => error.$message)"
      :loading="loadingRegistrate"
      v-model="registrationData.password"
      @change="v$.password.$validate()"
    />
    <TextField
      id="confirmPassword"
      type="password"
      :label="$t('message.page.auth.confirmPassword')"
      :placeholder="$t('message.page.auth.enterPassword')"
      :error="v$.confirmPassword.$error"
      :errorsText="v$.confirmPassword.$errors.map((error) => error.$message)"
      :loading="loadingRegistrate"
      v-model="registrationData.confirmPassword"
      @change="v$.confirmPassword.$validate()"
    />

    <div class="mt-auto">
      <Button
        block
        type="submit"
        :loading="loadingRegistrate"
      >
        {{ $t("message.page.auth.registrate") }}
      </Button>
    </div>
  </form>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue';
import { useVuelidate } from '@vuelidate/core'
import { required, helpers, sameAs } from '@vuelidate/validators'
import { useI18n } from 'vue-i18n'
import TextField from '@/components/ui/TextField.vue';
import Button from '@/components/ui/Button.vue';
import { useUserData } from '@/stores/user-data';

const { t } = useI18n()
const userData = useUserData()

const loadingRegistrate = ref(false)

const registrationData = reactive({
  username: "",
  displayName: "",
  password: "",
  confirmPassword: "",
})

const passwordsMatch = (value: string) => value === registrationData.password

const rules = {
  username: {
    required: helpers.withMessage(t("message.validations.fieldIsRequired"), required),
  },
  displayName: {
    required: helpers.withMessage(t("message.validations.fieldIsRequired"), required),
  },
  password: {
    required: helpers.withMessage(t("message.validations.fieldIsRequired"), required),
  },
  confirmPassword: {
    // sameAs: helpers.withMessage(t("message.validations.passwordsDontMatch"), sameAs("password")),
    sameAs: helpers.withMessage(t("message.validations.passwordsDontMatch"), passwordsMatch),
  }
}

const v$ = useVuelidate(rules, registrationData)

async function handleSubmit() {
  await v$.value.$validate()
  if (v$.value.$error) {
    return
  }
  loadingRegistrate.value = true
  try {
    await userData.registrate({
      username: registrationData.username,
      display_name: registrationData.displayName,
      password: registrationData.password,
    })
  } finally {
    loadingRegistrate.value = false
  }
}
</script>
