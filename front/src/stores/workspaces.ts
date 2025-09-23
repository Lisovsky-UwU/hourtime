import { defineStore } from "pinia";
import type { WorkspaceModel } from "./models/workspace";
import { useProjects } from "./projects";


export const useWorkspaces = defineStore("workspaces", {
  state: () => ({
    currentWorkspace: null as WorkspaceModel | null,

    projects: useProjects(),
  }),

  getters: {
    selectedWorkspace(): WorkspaceModel | null {
      return this.currentWorkspace
    }
  },

  actions: {
    async selectWorkspace(workspace: WorkspaceModel) {
      this.currentWorkspace = workspace

      const projects = useProjects()
      if (projects.projects !== null) {
        await projects.loadProjects()
      }
    }
  }
})
