import type { UserAccess } from "./common";
import type { WorkspaceModel } from "./workspace";

export interface OrganizationModel {
  organization_id: number,
  name: string,
  access: UserAccess,
  workspaces: WorkspaceModel[],
}

export interface OrganizationUpdateResponse  {
  id: number,
  name: string,
}

export interface OrganizationUpdateModel {
  organization_id: number,
  name: string,
}
