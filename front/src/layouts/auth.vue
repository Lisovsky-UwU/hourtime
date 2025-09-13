<template>
  <div class="bg-background h-screen w-full flex items-center justify-center">
    <div class="card">
      <div class="p-4 min-h-[430px] w-[350px] flex flex-col">
        <div class="flex justify-center">
          <Logo/>
        </div>
        <div class="flex justify-center mb-4">
          {{ $t("message.page.auth.loginToUse") }}
        </div>
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
            :loading="loadingAuth"
            v-model="loginData.username"
            @change="v$.username.$validate()"
          />
          <TextField
            id="password"
            type="password"
            :label="$t('message.page.auth.password')"
            :placeholder="$t('message.page.auth.enterPassword')"
            :error="v$.password.$error"
            :errorsText="v$.password.$errors.map((error) => error.$message)"
            :loading="loadingAuth"
            v-model="loginData.password"
            @change="v$.password.$validate()"
          />

          <div class="space-y-4 mt-auto">
            <Button
              block
              type="submit"
              :loading="loadingAuth"
            >
              {{ $t("message.page.auth.login") }}
            </Button>
            <Button
              block
              second
              outlined
              :disabled="loadingAuth"
            >
              {{ $t("message.page.auth.registrate") }}
            </Button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue';
import { useVuelidate } from '@vuelidate/core'
import { required, helpers } from '@vuelidate/validators'
import { useI18n } from 'vue-i18n'
import Logo from '@/components/ui/Logo.vue';
import TextField from '@/components/ui/TextField.vue';
import Button from '@/components/ui/Button.vue';

const { t } = useI18n()

const loadingAuth = ref(false)

const loginData = reactive({
  username: "",
  password: "",
})

const rules = {
  username: {
    required: helpers.withMessage(t("message.validations.fieldIsRequired"), required),
  },
  password: {
    required: helpers.withMessage(t("message.validations.fieldIsRequired"), required),
  },
}

const v$ = useVuelidate(rules, loginData)

async function handleSubmit() {
  await v$.value.$validate()
  if (v$.value.$error) {
    return
  }
  loadingAuth.value = true
}

</script>
