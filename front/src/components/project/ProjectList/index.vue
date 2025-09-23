<template>
  <ProjectElement
    v-for="project of projects.projects"
    :key="project.id"
    :project="project"
  />
</template>

<script setup lang="ts">
import ProjectElement from './ProjectElement.vue';
import { useProjects } from '@/stores/projects';

const projects = useProjects()
</script>
