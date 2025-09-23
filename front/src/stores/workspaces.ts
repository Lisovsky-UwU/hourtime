import { defineStore } from "pinia";
import type { WorkspaceModel } from "./models/workspace";
import { useProjects } from "./projects";
import { useOrganizations } from "./organizations";


export const useWorkspaces = defineStore("workspaces", {
  state: () => ({
    currentWorkspace: null as WorkspaceModel | null,
  }),

  getters: {
    selectedWorkspace(): WorkspaceModel | null {
      return this.currentWorkspace
    }
  },

  actions: {
    async selectWorkspace(workspace: WorkspaceModel) {
      this.currentWorkspace = workspace
      localStorage.setItem("SelectedWorkspace", String(this.currentWorkspace.id))

      const projects = useProjects()
      if (projects.projects !== null) {
        await projects.loadProjects()
      }
    },

    loadSavedSelect(): boolean {
      const organizations = useOrganizations()
      if (organizations.currentOrganization === null || organizations.currentOrganization.workspaces.length === null) {
        return false
      }

      const savedWorkspaceIdStr = localStorage.getItem("SelectedWorkspace")
      if (savedWorkspaceIdStr === null) {
        return false
      }

      const savedWorkspaceId = Number(savedWorkspaceIdStr)
      const savedWorkspace = organizations.currentOrganization.workspaces.find((item) => item.id === savedWorkspaceId)

      if (savedWorkspace === undefined) {
        return false
      }

      this.currentWorkspace = savedWorkspace
      return true
    },
  }
})
