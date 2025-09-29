import type { UserAccess } from "./common";

export interface WorkspaceModel {
  id: number,
  name: string,
}

export interface WorkspaceUpdateModel {
  workspace_id: number,
  name: string,
}

export interface WorkspaceForOrganizationResponse {
  access: UserAccess,
  workspaces: WorkspaceModel[],
}
