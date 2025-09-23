import { defineStore } from "pinia";
import type { OrganizationModel } from "./models/organization";
import { useApiStore } from "./api";
import { ApiEndpoint } from "./models/common";
import { useWorkspaces } from "./workspaces";
import type { WorkspaceModel } from "./models/workspace";


export const useOrganizations = defineStore("organizations", {
  state: () => ({
    organizations: null as null | OrganizationModel[],
    currentOrganization: null as null | OrganizationModel,

    apiStore: useApiStore(),
    workspaces: useWorkspaces(),
  }),

  getters: {
    myOrganizations(): OrganizationModel[] | null {
      return this.organizations
    },

    selectedOrganization(): OrganizationModel | null {
      return this.currentOrganization
    }
  },

  actions: {
    async setOrganizations(organizations: OrganizationModel[]) {
      this.organizations = organizations

      if (this.organizations.length > 0) {
        const savedLoad = this.loadSavedSelect()
        if (savedLoad) {
          const savedWorkspaceLoad = this.workspaces.loadSavedSelect()
          if (!savedWorkspaceLoad && this.currentOrganization !== null) {
            await this.workspaces.selectWorkspace(this.currentOrganization?.workspaces[0])
          }
        } else {
          await this.selectOrganization(this.organizations[0])
        }
      }
    },

    loadSavedSelect(): boolean {
      if (this.organizations === null || this.organizations.length === 0) {
        return false
      }

      const savedOrganizationIdStr = localStorage.getItem("SelectedOrganization")
      if (savedOrganizationIdStr === null) {
        return false
      }

      const savedOrganizationId = Number(savedOrganizationIdStr)
      const savedOrganization = this.organizations.find((item) => item.organization_id === savedOrganizationId)

      if (savedOrganization === undefined) {
        return false
      }

      this.currentOrganization = savedOrganization
      return true
    },

    async selectOrganization(organization: OrganizationModel, workspace: WorkspaceModel | null = null) {
      this.currentOrganization = organization
      localStorage.setItem("SelectedOrganization", String(this.currentOrganization.organization_id))
      if (workspace !== null) {
        await this.workspaces.selectWorkspace(workspace)
      } else if (organization.workspaces.length > 0) {
        await this.workspaces.selectWorkspace(organization.workspaces[0])
      }
    },

    async loadMyOrganizations() {
      const response: Array<OrganizationModel> = await this.apiStore.doRequest(
        ApiEndpoint.OrganizationMy,
        "GET",
      )
      await this.setOrganizations(response)
    },

    async createOrganization(name: string) {
      await this.apiStore.doRequest(
        ApiEndpoint.OrganizationCreate,
        "POST",
        { name }
      )
    },
  }
})
