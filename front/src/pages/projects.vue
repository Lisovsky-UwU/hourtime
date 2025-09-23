<template>
  <div>
    <div class="flex p-3">
      <div class="text-2xl">
        {{ $t("message.page.project.title") }}
      </div>
      <div class="flex-grow"/>
      <Button
        second
        class=""
        :disabled="loading"
      >
        {{ $t("message.common.create") }}
      </Button>
    </div>
  </div>

  <div v-if="loading" class="w-full justify-center flex items-center">
    <Loader />
  </div>

  <div v-else class="border-t border-border">
    <div
      v-if="projects.projects?.length === 0"
      class="w-full text-center mt-3 text-2xl text-text-muted"
    >
      {{ $t("message.page.project.noProjects") }}
    </div>
    <ProjectList v-else />
  </div>
</template>

<script setup lang="ts">
import { useProjects } from '@/stores/projects';
import { onMounted, ref, watch } from 'vue';
import Button from '@/components/ui/Button.vue';
import ProjectList from '@/components/project/ProjectList/index.vue'
import Loader from '@/components/ui/Loader.vue';

const projects = useProjects()
const loading = ref(true)

onMounted(async () => {
  if (projects.projects === null) {
    await projects.loadProjects()
  }
  loading.value = false
})

watch(
  () => projects.projects,
  (newValue) => {
    loading.value = newValue === null
  }
)
</script>
