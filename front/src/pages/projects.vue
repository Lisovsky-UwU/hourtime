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
        @click="doCreateProject"
      >
        <svg-icon type="mdi" :path="mdiPlus" />
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
    <ProjectList
      v-else
      @edit-project="doEditProject"
      @delete-project="doDeleteProject"
    />
  </div>

  <Dialog v-if="currentEditProject.projectData !== null" v-model="showEditDialog">
    <div class="flex flex-col gap-4">
      <EditProject
        v-model="currentEditProject.projectData"
        @updated="showEditDialog = false"
      />
      <Button
        block
        @click="showEditDialog = false"
      >
        {{ $t("message.common.cancel") }}
      </Button>
    </div>
  </Dialog>

  <Dialog v-model="showDeleteDialog">
    <div class="flex flex-col gap-4">
      <div class="text-xl">
        {{ $t("message.page.project.confirmDelete") }}
      </div>

      <div class="p-4 rounded-lg bg-bg-light flex flex-col">
        <div>
          {{ currentEditProject.projectData?.name }}
        </div>
      </div>

      <Button
        block
        color="danger"
        :loading="deleteLoading"
        @click="deleteProject"
      >
        {{ $t("message.common.delete") }}
      </Button>
      <Button
        block
        :disabled="deleteLoading"
        @click="showDeleteDialog = false"
      >
        {{ $t("message.common.cancel") }}
      </Button>
    </div>

  </Dialog>
</template>

<script setup lang="ts">
import { useProjects } from '@/stores/projects';
import { onMounted, reactive, ref, watch } from 'vue';
import Button from '@/components/ui/Button.vue';
import ProjectList from '@/components/project/ProjectList/index.vue'
import Loader from '@/components/ui/Loader.vue';
import SvgIcon from '@jamescoyle/vue-icon'
import { mdiPlus } from '@mdi/js';
import EditProject from '@/components/project/EditProject.vue';
import type { ProjectModel } from '@/stores/models/project';
import Dialog from '@/components/ui/Dialog.vue';

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

const showEditDialog = ref(false)
const showDeleteDialog = ref(false)
const currentEditProject = reactive({
  projectData: null as null | ProjectModel,
})

const deleteLoading = ref(false)

function doCreateProject() {
  currentEditProject.projectData = {
    id: null,
    name: "",
    description: null,
  }
  showEditDialog.value = true
}

function doEditProject(project: ProjectModel) {
  currentEditProject.projectData = {
    id: project.id,
    workspace_id: project.workspace_id,
    name: project.name,
    description: project.description,
  }
  showEditDialog.value = true
}

function doDeleteProject(project: ProjectModel) {
  currentEditProject.projectData = project
  showDeleteDialog.value = true
}

async function deleteProject() {
  if (currentEditProject.projectData !== null) {
    deleteLoading.value = true
    try {
      await projects.deleteProject(currentEditProject.projectData?.id)
      showDeleteDialog.value = false
    } finally {
      deleteLoading.value = false
    }
  }
}
</script>
