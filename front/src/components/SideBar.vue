<template>
  <div class="bg-surface p-1 flex flex-col">
    <button
      :title="$t('message.sideBar.timeTrack')"
      class="circle-button hover:bg-surface-hover"
      @click="router.push('/')"
    >
      <svg-icon type="mdi" :path="mdiClockTimeEight" />
    </button>
    <button
      :title="$t('message.sideBar.projects')"
      class="circle-button hover:bg-surface-hover"
      @click="router.push('/projects')"
    >
      <svg-icon type="mdi" :path="mdiBriefcase" />
    </button>
    <button
      :title="$t('message.sideBar.tasks')"
      class="circle-button hover:bg-surface-hover"
      @click="router.push('/tasks')"
    >
      <svg-icon type="mdi" :path="mdiCheckBold" />
    </button>
    <div class="flex-grow" />
    <button
      :title="$t('message.sideBar.logout')"
      class="circle-button hover:bg-surface-hover"
      @click="logout"
    >
      <Loader v-if="logoutLoading" type="circle" class="h-[20px] w-[20px]"/>
      <svg-icon v-else type="mdi" :path="mdiLogout" />
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import SvgIcon from '@jamescoyle/vue-icon'
import { mdiClockTimeEight, mdiBriefcase, mdiLogout, mdiCheckBold } from '@mdi/js';
import { useUserData } from '@/stores/user-data';
import Loader from './ui/Loader.vue';
import router from '@/router';

const userData = useUserData()

const logoutLoading = ref(false)

async function logout() {
  logoutLoading.value = true
  try {
    await userData.logout()
  } finally {
    logoutLoading.value = false
  }
}
</script>
