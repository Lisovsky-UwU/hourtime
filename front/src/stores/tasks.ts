import { defineStore } from "pinia";
import type { TaskCreateModel, TaskModel, TaskUpdateModel } from "./models/task";
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

    async createTask(task: TaskCreateModel) {
      const workspaces = useWorkspaces()
      if (workspaces.currentWorkspace === null) {
        return
      }
      const response: TaskModel = await this.apiStore.doRequest(
        ApiEndpoint.TaskCreate,
        "POST",
        {
          name: task.name,
          description: task.description,
          project_id: task.project_id,
          workspace_id: workspaces.currentWorkspace.id,
        },
      )
      if (this.currentTasks !== null) {
        this.currentTasks.push(response)
      }
    },

    async updateTask(taskData: TaskUpdateModel) {
      const response: TaskModel = await this.apiStore.doRequest(
        ApiEndpoint.TaskUpdate,
        "PUT",
        taskData
      )
      const task = this.currentTasks?.find((task) => task.id === response.id)
      if (task !== undefined) {
        task.name = response.name
        task.description = response.description
        task.project_id = response.project_id
      }
    },

    async deleteTask(taskId: string) {
      await this.apiStore.doRequest(
        ApiEndpoint.TaskDelete,
        "DELETE",
        null,
        { task_id: taskId }
      )
      const newTaskArr = this.currentTasks?.filter((task) => task.id !== taskId)
      if (newTaskArr !== undefined) {
        this.currentTasks = newTaskArr
      }
    }
  }
})
