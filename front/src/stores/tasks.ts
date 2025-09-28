import { defineStore } from "pinia";
import type { TaskModel } from "./models/task";
import { useApiStore } from "./api";
import { ApiEndpoint } from "./models/common";
import { useWorkspaces } from "./workspaces";

export const useTasks = defineStore("tasks", {
  state: () => ({
    currentTasks: null as TaskModel[] | null,

    apiStore: useApiStore()
  }),

  getters: {
    tasks(): TaskModel[] | null {
      return this.currentTasks
    }
  },

  actions: {
    async loadTasks() {
      this.currentTasks = null

      const workspaces = useWorkspaces()
      try {
        const response = await this.apiStore.doRequest(
          ApiEndpoint.TaskGetForWorkspace,
          "GET",
          null,
          { workspace_id: workspaces.selectedWorkspace?.id }
        )
        this.currentTasks = response
      } catch {
        this.currentTasks = []
      }
    },
  }
})
