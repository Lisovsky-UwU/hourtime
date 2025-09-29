import { defineStore } from "pinia";
import type { OrganizationModel, OrganizationUpdateModel, OrganizationUpdateResponse } from "./models/organization";
import { useApiStore } from "./api";
import { ApiEndpoint } from "./models/common";
import { useWorkspaces } from "./workspaces";
import type { WorkspaceForOrganizationResponse, WorkspaceModel } from "./models/workspace";


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

    async refreshWorkspaces(organization_id: number) {
      if (this.organizations === null) {
        return
      }
      const organization = this.organizations.find((org) => {
        return org.organization_id === organization_id
      })
      if (organization === undefined) {
        return
      }
      const response: WorkspaceForOrganizationResponse = await this.apiStore.doRequest(
        ApiEndpoint.WorkspaceGetForOrganization,
        "GET",
        null,
        {organization_id}
      )
      organization.access = response.access
      organization.workspaces = response.workspaces
    },

    async createOrganization(name: string): Promise<OrganizationUpdateResponse> {
     return await this.apiStore.doRequest(
        ApiEndpoint.OrganizationCreate,
        "POST",
        { name }
      )
    },

    async updateOrganization(organization: OrganizationUpdateModel): Promise<OrganizationUpdateResponse> {
      return await this.apiStore.doRequest(
        ApiEndpoint.OrganizationUpdate,
        "PUT",
        organization,
      )
    },

    async deleteOrganization(organization_id: number) {
      await this.apiStore.doRequest(
        ApiEndpoint.OrganizationDelete,
        "DELETE",
        null,
        {organization_id}
      )
    },
  }
})
