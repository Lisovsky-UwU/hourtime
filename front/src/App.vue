<template>
  <notifications
    classes="app-notification"
    position="top center"
    dangerously-set-inner-html
    width="400"
    duration="3"
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
  <router-view />
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import router from './router'
// import { notify } from '@kyvg/vue3-notification'
import SvgIcon from '@jamescoyle/vue-icon'
import {
  mdiInformation,
  mdiCheck,
  mdiAlert,
  mdiAlertBox,
  mdiClose,
} from '@mdi/js'

const iconByType = {
  success: mdiCheck,
  info: mdiInformation,
  warning: mdiAlert,
  error: mdiAlertBox,
}

onMounted(() => {
  // notify({
  //   title: "Test title",
  //   text: 'Test message <div class="text-4xl">SUCCESS</div>',
  //   type: "success"
  // })
  const userToken = localStorage.getItem("userToken")
  if (userToken === null) {
    router.push("/login")
  }
})
</script>
