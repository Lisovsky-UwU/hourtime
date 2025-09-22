<template>
  <div class="bg-bg-dark h-screen w-full flex items-center justify-center">
    <div class="card">
      <div class="p-4 min-h-[430px] w-[350px] flex flex-col">
        <div class="flex justify-center">
          <Logo/>
        </div>
        <div class="flex justify-center mb-4">
          {{ $t("message.page.auth.loginToUse") }}
        </div>
        <Login v-if="selectedMethod === 'login'" />
        <Registrate v-else />

        <Button
          block
          second
          outlined
          class="mt-4"
          @click="selectedMethod === 'login' ? selectedMethod = 'registrate' : selectedMethod = 'login'"
        >
          <div v-if="selectedMethod === 'login'">
            {{ $t("message.page.auth.goRegistrate") }}
          </div>
          <div v-else>
            {{ $t("message.page.auth.goLogin") }}
          </div>
        </Button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import Logo from '@/components/ui/Logo.vue';
import Button from '@/components/ui/Button.vue';
import Login from '@/components/auth/Login.vue';
import Registrate from '@/components/auth/Registrate.vue';

const selectedMethod = ref("login")

</script>
