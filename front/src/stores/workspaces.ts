import { defineStore } from "pinia";
import type { WorkspaceModel } from "./models/workspace";

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
    selectWorkspace(workspace: WorkspaceModel) {
      this.currentWorkspace = workspace
    }
  }
})
