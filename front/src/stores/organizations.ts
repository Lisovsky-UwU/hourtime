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
    setOrganizations(organizations: OrganizationModel[]) {
      this.organizations = organizations
      if (organizations.length > 0) {
        this.selectOrganization(organizations[0])
      }
    },

    selectOrganization(organization: OrganizationModel, workspace: WorkspaceModel | null = null) {
      this.currentOrganization = organization
      if (workspace !== null) {
        this.workspaces.selectWorkspace(workspace)
      } else if (organization.workspaces.length > 0) {
        this.workspaces.selectWorkspace(organization.workspaces[0])
      }
    },

    async loadMyOrganizations() {
      const response: Array<OrganizationModel> = await this.apiStore.doRequest(
        ApiEndpoint.OrganizationMy,
        "GET",
      )
      this.setOrganizations(response)
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
