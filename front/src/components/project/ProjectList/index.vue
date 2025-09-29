<template>
  <ProjectElement
    v-for="project of projects.projects"
    :key="project.id"
    :project="project"
    @edit-project="(project) => emit('editProject', project)"
    @delete-project="(project) => emit('deleteProject', project)"
  />
</template>

<script setup lang="ts">
import ProjectElement from './ProjectElement.vue';
import { useProjects } from '@/stores/projects';

const emit = defineEmits(["editProject", "deleteProject"])

const projects = useProjects()
</script>
