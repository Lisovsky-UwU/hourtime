import { defineStore } from "pinia";
import type { ProjectModel } from "./models/project";
import { useWorkspaces } from "./workspaces";
import { useApiStore } from "./api";
import { ApiEndpoint } from "./models/common";


export const useProjects = defineStore("projects", {
  state: () => ({
    currentProjects: null as ProjectModel[] | null,

    apiStore: useApiStore(),
  }),

  getters: {
    projects(): ProjectModel[] | null {
      return this.currentProjects
    },

    projectsMap(): {number: ProjectModel} | null {
      if (this.currentProjects === null) {
        return null
      }
      return this.currentProjects.reduce((acc, element) => {
        acc[element.id] = element
        return acc
      }, {} as {number: ProjectModel})
    }
  },

  actions: {
    async loadProjects() {
      this.currentProjects = null
      const workspaces = useWorkspaces()

      try {
        const response = await this.apiStore.doRequest(
          ApiEndpoint.ProjectGetForWorkspace,
          "GET",
          null,
          { workspace_id: workspaces.selectedWorkspace?.id }
        )
        this.currentProjects = response
      } catch {
        this.currentProjects = []
      }
    },
  }
})
