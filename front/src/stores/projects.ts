import { defineStore } from "pinia";
import type { ProjectCreateModel, ProjectModel, ProjectUpdateModel } from "./models/project";
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

    async createProject(project: ProjectCreateModel) {
      const workspaces = useWorkspaces()
      const newProject: ProjectModel = await this.apiStore.doRequest(
        ApiEndpoint.ProjectCreate,
        "POST",
        {
          workspace_id: workspaces.currentWorkspace?.id,
          name: project.name,
          description: project.description,
        },
      )
      if (this.projects !== null) {
        this.projects.push(newProject)
      }
    },

    async updateProject(projectData: ProjectUpdateModel) {
      const projectNewData: ProjectModel = await this.apiStore.doRequest(
        ApiEndpoint.ProjectUpdate,
        "PUT",
        projectData,
      )
      const project = this.currentProjects?.find((prj) => {
        return prj.id === projectNewData.id
      })

      if (project !== undefined) {
        project.name = projectNewData.name
        project.description = projectNewData.description
      }
    },

    async deleteProject(projectId: number) {
      await this.apiStore.doRequest(
        ApiEndpoint.ProjectDelete,
        "DELETE",
        null,
        { project_id: projectId },
      )
      const newArr = this.currentProjects?.filter((prj) => prj.id !== projectId)
      if (newArr !== undefined) {
        this.currentProjects = newArr
      }
    }
  }
})
