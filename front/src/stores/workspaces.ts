import { defineStore } from "pinia";
import type { WorkspaceModel, WorkspaceUpdateModel } from "./models/workspace";
import { useProjects } from "./projects";
import { useOrganizations } from "./organizations";
import { useTasks } from "./tasks";
import { useApiStore } from "./api";
import { ApiEndpoint } from "./models/common";


export const useWorkspaces = defineStore("workspaces", {
  state: () => ({
    currentWorkspace: null as WorkspaceModel | null,

    apiStore: useApiStore(),
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
      const tasks = useTasks()

      const promisesForLoad = []
      if (projects.projects !== null) {
        promisesForLoad.push(projects.loadProjects())
      }
      if (tasks.tasks !== null) {
        promisesForLoad.push(tasks.loadTasks())
      }

      if (promisesForLoad.length > 0) {
        await Promise.all(promisesForLoad)
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

    async createWorkspace(name: string, organization_id: number): Promise<WorkspaceModel> {
      return await this.apiStore.doRequest(
        ApiEndpoint.WorkspaceCreate,
        "POST",
        {name, organization_id}
      )
    },

    async updateWorkspace(workspaceData: WorkspaceUpdateModel): Promise<WorkspaceModel> {
      return await this.apiStore.doRequest(
        ApiEndpoint.WorkspaceUpdate,
        "PUT",
        workspaceData,
      )
    },

    async deleteWorkspace(workspaceId: number) {
      await this.apiStore.doRequest(
        ApiEndpoint.WorkspaceDelete,
        "DELETE",
        null,
        {workspace_id: workspaceId}
      )
    },
  }
})
