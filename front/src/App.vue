<template>
  <notifications
    classes="app-notification"
    position="top center"
    dangerously-set-inner-html
    width="500"
    :duration="5000"
  >
    <template v-slot:body="{ item, close }">
      <div :class="`app-notification ${item.type}`">
        <div class="flex flex-row items-center gap-3">
          <svg-icon size="30" type="mdi" :path="iconByType[item.type]" />
          <div class="flex flex-col flex-grow">
            <div class="notification-title">
              {{ item.title }}
            </div>

            <div class="notification-content" v-html="item.text" />
          </div>
          <svg-icon type="mdi" :path="mdiClose" @click="close" />
        </div>
      </div>
    </template>
  </notifications>
  <div class="bg-background text-primary-text">
    <div v-if="loading" class="h-screen w-screen flex justify-center items-center">
      <Loader/>
    </div>
    <component v-else :is="currentLayout">
      <router-view />
    </component>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
// import { notify } from '@kyvg/vue3-notification'
import SvgIcon from '@jamescoyle/vue-icon'
import {
  mdiInformation,
  mdiCheck,
  mdiAlert,
  mdiAlertBox,
  mdiClose,
} from '@mdi/js'
import Loader from './components/ui/Loader.vue'
import { useApiStore } from './stores/api'
import { useUserData } from './stores/user-data'

import AuthLayout from './layouts/auth.vue'
import DefaultLayout from './layouts/default.vue'

const loading = ref(true)

const iconByType = {
  success: mdiCheck,
  info: mdiInformation,
  warning: mdiAlert,
  error: mdiAlertBox,
}

const api = useApiStore()
const userData = useUserData()

const currentLayout = computed(() => api.isLogin ? DefaultLayout : AuthLayout)

onMounted(async () => {
  // notify({
  //   title: "Test title",
  //   text: 'Test message <div class="text-4xl">SUCCESS</div>',
  //   type: "success"
  // })

  try {
    api.loadToken()
    if (api.isLogin) {
      await userData.loadMyData()
    }
  } finally {
    loading.value = false
  }
})
</script>
