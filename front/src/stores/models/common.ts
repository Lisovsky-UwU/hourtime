export interface ErrorResponse {
  error_type: string,
  error_code: number,
  user_message: string,
  detail: string | null,
}

export enum UserAccess {
  Owner = "Owner",
  Full = "Full Access",
  Partial = "Partial Access"
}

export enum ApiEndpoint {
  AuthLogin = "/auth/login",
  AuthRegistrate = "/auth/registrate",
  AuthLogout = "/auth/logout",

  UserMyInfo = "/user/me/info",
  UserMeChangePassword = "/user/me/change_password",
  UserMeUpdate = "/user/me/update",

  OrganizationCreate = "/organization/create",
  OrganizationMy = "/organization/my",
  OrganizationUpdate = "/organization/update",
  OrganizationDelete = "/organization/delete",

  WorkspaceCreate = "/workspace/create",
  WorkspaceGetForOrganization = "/workspace/for_organization",
  WorkspaceUpdate = "/workspace/update",
  WorkspaceDelete = "/workspace/delete",

  ProjectCreate = "/project/create",
  ProjectGetForWorkspace = "/project/for_workspace",
  ProjectUpdate = "/project/update",
  ProjectDelete = "/project/delete",

  TaskCreate = "/task/create",
  TaskGetForWorkspace = "/task/for_workspace",
  TaskUpdate = "/task/update",
  TaskDelete = "/task/delete",

  TimeEntryStart = "/time_entry/start",
  TimeEntryGetMy = "/time_entry/get_my",
  TimeEntryGetMyForDates = "/time_entry/get_my_for_dates",
  TimeEntryUpdate = "/time_entry/update",
  TimeEntryDelete = "/time_entry/delete",
}
